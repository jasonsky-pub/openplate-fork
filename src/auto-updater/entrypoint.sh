#!/bin/bash
##
##              Copyright 2025 Comcast Cable Communications Management, LLC
##
##              Licensed under the Apache License, Version 2.0 (the "License");
##              you may not use this file except in compliance with the License.
##              You may obtain a copy of the License at
##
##              http://www.apache.org/licenses/LICENSE-2.0
##
##              Unless required by applicable law or agreed to in writing, software
##              distributed under the License is distributed on an "AS IS" BASIS,
##              WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##              See the License for the specific language governing permissions and
##              limitations under the License.
##
##              SPDX-License-Identifier: Apache-2.0
##
##              This product includes software developed at Comcast (https://www.comcast.com/).##


# Define a cleanup function
cleanup() {
    echo "Cleaning up SSH key..."
    if command -v shred > /dev/null; then
        shred -vzun1 ~/.ssh/id_rsa
    else
        rm -f ~/.ssh/id_rsa
    fi
}

echo PWD=`pwd`
# echo START OF FIND ----------------------
# find .
# echo END OF FIND ----------------------

AUTO_PR_APPROVAL=${AUTO_PR_APPROVAL:-true}
echo "AUTO_PR_APPROVAL: $AUTO_PR_APPROVAL"

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
	echo "No GITHUB_TOKEN found, exiting"
	exit 1
fi

#check ssh key
if [ -z "$SSH_KEY" ]; then
	echo "No SSH key found, exiting"
	exit 1
fi

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_PR_APPROVAL_TOKEN" ]; then
	echo "No GITHUB PR APPROVAL TOKEN found, exiting"
	exit 1
fi

echo "Setting up SSH----------"
export REAL_USER=`whoami`
echo setting user to $REAL_USER
# print the getent passwd output 
echo `getent passwd`
export REAL_HOME=`getent passwd | grep "^$REAL_USER:" | cut -d ":" -f 6`
echo setting $HOME to $REAL_HOME
export HOME=$REAL_HOME

mkdir -p ~/.ssh/
chmod 700 ~/.ssh
echo "$SSH_KEY" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa
touch ~/.ssh/known_hosts
ssh-keygen -R github.com
ssh-keyscan -t rsa -H github.com >> ~/.ssh/known_hosts
git config user.email "${GIT_USER_EMAIL:-noreply@github.com}"
git config user.name "${GIT_USER_NAME:-openplate}"

# check if the ssh key is valid and can connect to github
ssh -i ~/.ssh/id_rsa -T git@github.com

echo "starting Openplate update"

# Register the cleanup function to be called on script exit
trap cleanup EXIT

set -e

export BRANCH_NAME="chore/openplate-update"
PR_BODY_TEMPLATE_PATH="/app/pr-body.md.tmpl"

# Ensure the Git remote URL uses SSH (required for git push/delete operations)
CURRENT_URL=$(git config --get remote.origin.url)

echo "Current remote URL: $CURRENT_URL"

# Check if the URL is using HTTPS
if [[ "$CURRENT_URL" == https://github.com/* ]]; then
	# Extract the repository owner and name from the HTTPS URL
	REPO_PATH=$(echo "$CURRENT_URL" | sed -E 's|https://github.com/([^/]+/[^/]+)$|\1|; s|https://github.com/([^/]+/[^/]+)\.git$|\1|')

	# Construct the SSH URL
	SSH_URL="git@github.com:$REPO_PATH.git"
	echo "Changing remote URL to SSH: $SSH_URL"
	# Update the remote URL to use SSH
	git remote set-url origin "$SSH_URL"
else
	echo "Remote URL is already using SSH or another protocol: $CURRENT_URL"
fi

git config --global --add safe.directory "$(pwd)"

echo "Fetching all refs and tags"
git fetch --all --prune --tags

echo "Cleaning up any existing PR/branch for $BRANCH_NAME (always)"
set +e

# If we're currently on the branch we're about to delete, detach first
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$CURRENT_BRANCH" = "$BRANCH_NAME" ]; then
	echo "Currently on $BRANCH_NAME; checking out detached HEAD before cleanup"
	git checkout --detach
fi

# Close any open PRs for this branch (and request branch deletion via GH)
PR_NUMBERS=$(gh pr list --state open --head "$BRANCH_NAME" --json number --jq '.[].number' 2>/dev/null)
LIST_EXIT=$?
if [ $LIST_EXIT -ne 0 ]; then
	echo "Warning: could not list PRs for head '$BRANCH_NAME' (gh pr list exit $LIST_EXIT); continuing cleanup"
fi

for PR in $PR_NUMBERS; do
	echo "Closing PR #$PR for $BRANCH_NAME"
	gh pr close "$PR" --delete-branch --comment "Closing stale auto-updater PR; do not touch this pr or branch" 2>/dev/null
done

# Delete remote branch only if it exists
git ls-remote --exit-code --heads origin "$BRANCH_NAME" > /dev/null 2>&1
REMOTE_BRANCH_EXISTS=$?
if [ $REMOTE_BRANCH_EXISTS -eq 0 ]; then
	echo "Deleting remote branch $BRANCH_NAME"
	git push origin --delete "$BRANCH_NAME" 2>/dev/null
else
	echo "Remote branch $BRANCH_NAME does not exist; skipping remote delete"
fi

# Delete local branch only if it exists
git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"
LOCAL_BRANCH_EXISTS=$?
if [ $LOCAL_BRANCH_EXISTS -eq 0 ]; then
	echo "Deleting local branch $BRANCH_NAME"
	git branch -D "$BRANCH_NAME" 2>/dev/null
else
	echo "Local branch $BRANCH_NAME does not exist; skipping local delete"
fi

set -e

echo "Detecting destination repo default branch"
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
if [ -z "$DEFAULT_BRANCH" ]; then
	DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null)
fi

if [ -z "$DEFAULT_BRANCH" ]; then
	echo "Could not determine default branch from origin/GitHub; exiting without changes."
	exit 0
fi

echo "Detected default branch: $DEFAULT_BRANCH"

set +e
# Check for openplate changes (performed after cleanup)
OPENPLATE_HASH=`openplate -a project verify`
OPENPLATE_RESULT=$?
set -e

echo "OPENPLATE_HASH: $OPENPLATE_HASH"
echo "OPENPLATE_RESULT: $OPENPLATE_RESULT"

if [ $OPENPLATE_RESULT -ne 0 ] && [ $OPENPLATE_RESULT -ne 255 ]; then
	echo "ERROR returned from Openplate, exiting"
	exit -1
fi

if [ $OPENPLATE_RESULT -eq 0 ]; then
	echo "NO difference found (cleanup complete; no PR/branch remains)"
	exit 0
fi

echo "Found outstanding template changes for update hash: $OPENPLATE_HASH"

echo "Updating local default branch: $DEFAULT_BRANCH"
git fetch --all --prune --tags
git checkout "$DEFAULT_BRANCH"
git pull --ff-only origin "$DEFAULT_BRANCH"

echo "Creating update branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Apply the openplate changes
openplate -a project update
git add -A
git commit -m "Applying Openplate Template Updates, hash: $OPENPLATE_HASH"
git push -u origin "$BRANCH_NAME"

export BRANCH_DATE=`date +%Y%m%d`

RUN_DATE_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ ! -f "$PR_BODY_TEMPLATE_PATH" ]; then
	echo "ERROR: PR body template not found at $PR_BODY_TEMPLATE_PATH"
	exit 1
fi

PR_BODY=$(cat "$PR_BODY_TEMPLATE_PATH")
PR_BODY="${PR_BODY//\{\{BRANCH_NAME\}\}/$BRANCH_NAME}"
PR_BODY="${PR_BODY//\{\{DEFAULT_BRANCH\}\}/$DEFAULT_BRANCH}"
PR_BODY="${PR_BODY//\{\{OPENPLATE_HASH\}\}/$OPENPLATE_HASH}"
PR_BODY="${PR_BODY//\{\{RUN_DATE_UTC\}\}/$RUN_DATE_UTC}"

set +e
PR_NUMBER=$(gh pr create \
	--title "Template Update - $BRANCH_DATE (do not touch this pr or branch)" \
	--body "$PR_BODY" \
	--head "$BRANCH_NAME" \
	--base "$DEFAULT_BRANCH")
CREATE_EXIT=$?
set -e

if [ $CREATE_EXIT -ne 0 ] || [ -z "$PR_NUMBER" ]; then
	echo "Failed to create PR (exit $CREATE_EXIT). Attempting to locate an existing PR for $BRANCH_NAME."
	PR_NUMBER=$(gh pr list --state all --head "$BRANCH_NAME" --limit 1 --json url --jq '.[0].url' 2>/dev/null)
	if [ -z "$PR_NUMBER" ]; then
		echo "Could not create or locate a PR for $BRANCH_NAME"
		exit 1
	fi
fi

echo "PR created/found: $PR_NUMBER"

echo "merging PR"

# Merge the PR automatically
gh pr merge --auto --merge --delete-branch "$PR_NUMBER"

# if AUTO PR APPROVAL is set to true, approve the PR (existing behavior)
if [ "$AUTO_PR_APPROVAL" = "true" ]; then
	echo "approving PR"

	#Change the TOKEN to the PR approval token
	ORIGINAL_GITHUB_TOKEN="$GITHUB_TOKEN"
	export GITHUB_TOKEN=$GITHUB_PR_APPROVAL_TOKEN

	#Check current user
	USER_NAME=`gh api user | jq -r .login`
	echo "Current user: $USER_NAME"

	# Approve the PR automatically
	gh pr review --approve "$PR_NUMBER"

	# Restore original token
	export GITHUB_TOKEN="$ORIGINAL_GITHUB_TOKEN"
else
	echo "AUTO PR APPROVAL is set to false, skipping approval"
fi
