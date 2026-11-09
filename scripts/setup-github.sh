#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'HELP'
Usage: bash scripts/setup-github.sh --mode standard|lite --repo OWNER/REPO \
  --owner OWNER (--project NUMBER | --create-project --title TITLE) [options]

Preview by default. --apply permits schema creation and repository linking.
  --dry-run               Explicit preview; incompatible with --apply
  --initialize-empty      Allow Status initialization only on an empty Project
  --allow-public-project  Permit applying to an explicitly selected public Project
No workflow files are installed and no existing cards are migrated.
HELP
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
need_value() {
    [ "$#" -ge 2 ] && [ -n "$2" ] && [[ "$2" != --* ]] ||
        fail "$1 requires a value."
}

MODE="" REPO="" OWNER="" NUMBER="" TITLE=""
APPLY=false DRY_RUN=false CREATE=false INITIALIZE=false ALLOW_PUBLIC=false
while [ "$#" -gt 0 ]; do
    case "$1" in
        --mode) need_value "$@"; MODE="$2"; shift 2 ;;
        --repo) need_value "$@"; REPO="$2"; shift 2 ;;
        --owner) need_value "$@"; OWNER="$2"; shift 2 ;;
        --project) need_value "$@"; NUMBER="$2"; shift 2 ;;
        --title) need_value "$@"; TITLE="$2"; shift 2 ;;
        --apply) APPLY=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --create-project) CREATE=true; shift ;;
        --initialize-empty) INITIALIZE=true; shift ;;
        --allow-public-project) ALLOW_PUBLIC=true; shift ;;
        --help|-h) usage; exit 0 ;;
        *) fail "Unknown argument: $1" ;;
    esac
done

[[ "$MODE" == standard || "$MODE" == lite ]] || fail "Select --mode standard or lite."
[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail "Use --repo OWNER/REPOSITORY."
[[ "$OWNER" =~ ^[A-Za-z0-9_-]+$ ]] || fail "Select an explicit --owner login."
if $CREATE; then
    [ -z "$NUMBER" ] && [ -n "$TITLE" ] ||
        fail "Use --create-project with --title, not --project."
    [[ "$TITLE" != *$'\n'* && "$TITLE" != *$'\t'* && "$TITLE" != *$'\r'* ]] ||
        fail "Project title must be a single line without tabs."
else
    [[ "$NUMBER" =~ ^[1-9][0-9]*$ ]] || fail "Select --project NUMBER or --create-project."
    [ -z "$TITLE" ] || fail "--title requires --create-project."
fi
if $APPLY && $DRY_RUN; then fail "Use either --apply or --dry-run."; fi
command -v gh >/dev/null 2>&1 || fail "Install gh and authenticate with repository and Project access."
STEP="authentication"
trap 'printf "GitHub setup failed during %s. No workflow files were installed.\n" "$STEP" >&2' ERR
gh auth status >/dev/null

STEP="repository preflight"
META="$(gh api "repos/$REPO" --jq '[.has_issues, .permissions.push, .private] | @tsv')"
IFS=$'\t' read -r ISSUES WRITE PRIVATE_REPO <<< "$META"
[ "$ISSUES" = true ] || fail "Enable repository Issues before setup."
[ "$WRITE" = true ] || fail "Repository write access is required for $REPO."
printf 'Mode: %s\nRepository: %s (private=%s)\n' "$MODE" "$REPO" "$PRIVATE_REPO"

if $CREATE; then
    STEP="Project lookup"
    COUNT="$(gh project list --owner "$OWNER" --limit 1000 --format json --jq '.totalCount')"
    [[ "$COUNT" =~ ^[0-9]+$ ]] && [ "$COUNT" -le 1000 ] ||
        fail "Project inventory is incomplete; select a Project number explicitly."
    LIST="$(gh project list --owner "$OWNER" --limit 1000 --format json --jq '.projects[] | [.number, .title] | @tsv')"
    MATCHES=0
    while IFS=$'\t' read -r N T; do
        if [ "$T" = "$TITLE" ]; then NUMBER="$N"; MATCHES=$((MATCHES + 1)); fi
    done <<< "$LIST"
    [ "$MATCHES" -le 1 ] || fail "Multiple Projects have that title; select --project NUMBER."
fi

EXPECTED=$'Inbox\nShaping\nReady\nIn progress\nIn review\nBlocked\nDone'
NAMES=("Work Type" "Priority")
OPTIONS=("Idea,Feature,Task" "High,Medium,Low")
if [ "$MODE" = standard ]; then
    NAMES+=("Stage" "Review Verdict" "Brief Link" "Release Note Link")
    OPTIONS+=("Requirements,Architecture,Build,Review,Deliver" "Pending,Accepted,Changes requested,Blocked" "" "")
fi
CREATED=false
if [ -z "$NUMBER" ]; then
    if ! $APPLY; then
        printf 'Preview: create private Project "%s" for %s.\n' "$TITLE" "$OWNER"
        printf 'Preview Status: %s\n' "$(printf '%s' "$EXPECTED" | tr '\n' ',')"
        for ((I=0; I<${#NAMES[@]}; I++)); do
            printf 'Preview field: %s (%s)\n' "${NAMES[$I]}" "${OPTIONS[$I]:-TEXT}"
        done
        printf 'Preview: link repository %s.\n' "$REPO"
        printf 'Preview only. No local or remote changes. Workflow installation has not run.\n'
        exit 0
    fi
    STEP="Project owner lookup"
    OWNER_ID="$(gh api graphql \
        -f query='query($login:String!){repositoryOwner(login:$login){id}}' \
        -f login="$OWNER" --jq '.data.repositoryOwner.id')"
    [ -n "$OWNER_ID" ] && [ "$OWNER_ID" != null ] ||
        fail "Could not resolve Project owner $OWNER; no Project was created."
    STEP="Project creation"
    NUMBER="$(gh api graphql \
        -f query='mutation($ownerId:ID!,$title:String!){createProjectV2(input:{ownerId:$ownerId,title:$title}){projectV2{number}}}' \
        -f ownerId="$OWNER_ID" -f title="$TITLE" \
        --jq '.data.createProjectV2.projectV2.number')"
    [[ "$NUMBER" =~ ^[1-9][0-9]*$ ]] || fail "Creation did not return a Project number; inspect GitHub before retrying."
    CREATED=true
    printf 'Created Project #%s. If a later step fails, retry using this number.\n' "$NUMBER"
fi

STEP="Project preflight"
META="$(gh project view "$NUMBER" --owner "$OWNER" --format json --jq '[.id, .url, .closed, .public] | @tsv')"
IFS=$'\t' read -r PROJECT_ID PROJECT_URL CLOSED PUBLIC <<< "$META"
[[ "$PROJECT_ID" =~ ^PVT_[A-Za-z0-9_-]+$ ]] || fail "Invalid Project identity returned."
[ "$CLOSED" = false ] || fail "Project #$NUMBER is closed."
CAN_UPDATE="$(gh api graphql -f query='query($id:ID!){node(id:$id){... on ProjectV2{viewerCanUpdate}}}' -f id="$PROJECT_ID" --jq '.data.node.viewerCanUpdate')"
[ "$CAN_UPDATE" = true ] || fail "Project update access is required."
if $APPLY && [ "$PUBLIC" = true ] && ! $ALLOW_PUBLIC; then
    fail "Project is public. Review visibility and explicitly pass --allow-public-project to apply."
fi
printf 'Project: %s (public=%s)\n' "$PROJECT_URL" "$PUBLIC"

field_id() {
    gh project field-list "$NUMBER" --owner "$OWNER" --limit 100 --format json \
        --jq ".fields[] | select(.name == \"$1\") | .id"
}
field_options() {
    gh project field-list "$NUMBER" --owner "$OWNER" --limit 100 --format json \
        --jq ".fields[] | select(.name == \"$1\") | .options[]?.name"
}
same_options() {
    [ "$(printf '%s\n' "$1" | LC_ALL=C sort)" = "$(printf '%s\n' "$2" | LC_ALL=C sort)" ]
}
FIELD_COUNT="$(gh project field-list "$NUMBER" --owner "$OWNER" --limit 100 --format json --jq '.totalCount')"
[[ "$FIELD_COUNT" =~ ^[0-9]+$ ]] && [ "$FIELD_COUNT" -le 100 ] ||
    fail "Field inventory is incomplete; reconcile this Project before setup."
STATUS_ID="$(field_id Status)"
[[ "$STATUS_ID" =~ ^PVTSSF_[A-Za-z0-9_-]+$ ]] || fail "Expected one single-select Status field."
ACTUAL="$(field_options Status)"
RESET=false
if ! same_options "$ACTUAL" "$EXPECTED"; then
    ITEM_COUNT="$(gh project view "$NUMBER" --owner "$OWNER" --format json --jq '.items.totalCount')"
    if [ "$ITEM_COUNT" != 0 ]; then
        fail "Status schema differs on a populated Project. Use a separate previewed migration; no states were reset."
    fi
    if ! $CREATED && ! $INITIALIZE; then
        fail "Status schema differs. For this empty Project only, --initialize-empty permits initialization."
    fi
    RESET=true
fi

# Validate all existing fields before making any schema changes.
for ((I=0; I<${#NAMES[@]}; I++)); do
    NAME="${NAMES[$I]}" OPTION="${OPTIONS[$I]}"
    ID="$(field_id "$NAME")"
    [ -n "$ID" ] || continue
    if [ -n "$OPTION" ]; then
        [[ "$ID" =~ ^PVTSSF_[A-Za-z0-9_-]+$ ]] || fail "$NAME must be one single-select field."
        same_options "$(field_options "$NAME")" "$(printf '%s' "$OPTION" | tr ',' '\n')" ||
            fail "$NAME options differ; reconcile explicitly before setup."
    else
        [[ "$ID" =~ ^PVTF_[A-Za-z0-9_-]+$ ]] || fail "$NAME must be one text field."
        TYPE="$(gh api graphql -f query='query($id:ID!){node(id:$id){... on ProjectV2Field{dataType}}}' -f id="$ID" --jq '.data.node.dataType')"
        [ "$TYPE" = TEXT ] || fail "$NAME must be text, not $TYPE."
    fi
done

if $RESET; then
    printf '%s: initialize the seven shared Status values on empty Project #%s.\n' "$($APPLY && printf Apply || printf Preview)" "$NUMBER"
    printf 'Status options: %s\n' "$(printf '%s' "$EXPECTED" | tr '\n' ',')"
    if $APPLY; then
        STEP="Status initialization on Project #$NUMBER"
        [ "$(gh project view "$NUMBER" --owner "$OWNER" --format json --jq '.items.totalCount')" = 0 ] ||
            fail "Project acquired items during setup; no Status options were reset."
        same_options "$(field_options Status)" "$ACTUAL" ||
            fail "Status options changed during setup; inspect the Project and retry."
        printf '{"query":"mutation($id:ID!,$options:[ProjectV2SingleSelectFieldOptionInput!]!){updateProjectV2Field(input:{fieldId:$id,singleSelectOptions:$options}){clientMutationId}}","variables":{"id":"%s","options":[{"name":"Inbox","color":"GRAY","description":"Captured work"},{"name":"Shaping","color":"PURPLE","description":"Requirements or architecture"},{"name":"Ready","color":"BLUE","description":"Readiness gates satisfied"},{"name":"In progress","color":"YELLOW","description":"Assigned implementation"},{"name":"In review","color":"ORANGE","description":"Review and delivery pending"},{"name":"Blocked","color":"RED","description":"Recorded impediment"},{"name":"Done","color":"GREEN","description":"Verified delivery"}]}}' "$STATUS_ID" |
            gh api graphql --input - >/dev/null
    fi
fi
for ((I=0; I<${#NAMES[@]}; I++)); do
    NAME="${NAMES[$I]}" OPTION="${OPTIONS[$I]}"
    ID="$(field_id "$NAME")"
    if [ -z "$ID" ]; then
        printf 'Missing field: %s (%s)\n' "$NAME" "${OPTION:-TEXT}"
        if $APPLY; then
            STEP="creating $NAME on Project #$NUMBER"
            if [ -n "$OPTION" ]; then
                gh project field-create "$NUMBER" --owner "$OWNER" --name "$NAME" \
                    --data-type SINGLE_SELECT --single-select-options "$OPTION" >/dev/null
            else
                gh project field-create "$NUMBER" --owner "$OWNER" --name "$NAME" --data-type TEXT >/dev/null
            fi
        fi
    fi
done
if ! $APPLY; then
    printf 'Preview: ensure repository link to %s.\n' "$REPO"
    printf 'Preview only. No local or remote changes. Workflow installation has not run.\n'
    exit 0
fi

STEP="repository linking on Project #$NUMBER"
gh project link "$NUMBER" --owner "$OWNER" --repo "$REPO"
STEP="final verification on Project #$NUMBER"
same_options "$(field_options Status)" "$EXPECTED" || fail "Status readback did not match."
for ((I=0; I<${#NAMES[@]}; I++)); do
    NAME="${NAMES[$I]}"
    ID="$(field_id "$NAME")"
    [ -n "$ID" ] || fail "Missing field after apply: $NAME."
    if [ -n "${OPTIONS[$I]}" ]; then
        same_options "$(field_options "$NAME")" "$(printf '%s' "${OPTIONS[$I]}" | tr ',' '\n')" ||
            fail "Options readback did not match for $NAME."
    fi
done
LINKED="$(gh api graphql -f query='query($id:ID!,$owner:String!,$repo:String!){node(id:$id){... on ProjectV2{repositories(first:100){nodes{nameWithOwner} pageInfo{hasNextPage}}}} repository(owner:$owner,name:$repo){nameWithOwner}}' -f id="$PROJECT_ID" -f owner="${REPO%/*}" -f repo="${REPO#*/}" --jq '.data as $d | any($d.node.repositories.nodes[]; .nameWithOwner == $d.repository.nameWithOwner)')"
[ "$LINKED" = true ] || fail "Repository link was not confirmed in readback."
printf 'GitHub backlog verified: %s\nMode: %s\n' "$PROJECT_URL" "$MODE"
printf 'No workflow files installed. Next: install the selected workflow assets when that phase is available.\n'
