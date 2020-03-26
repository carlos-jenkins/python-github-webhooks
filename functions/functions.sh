function get_configuration_allinconfig {

    # Set subs_allinconfig var
    subs_allinconfig=""

    # Check configuration repository
    #git ls-remote "https://${GITHUB_USER}:${GITHUB_TOKEN}@${REPO_URL#https://}-config.git" &> /dev/null
    curl -s --user "${GITHUB_USER}:${GITHUB_TOKEN}" "https://api.github.com/repos/${ORG_NAME}/${REPO_NAME}-config/branches" | jq '.[] | .name' 2> /dev/null | grep -wq "master"

    if [ $? -eq 0 ]; then

        echo "Getting configuration of allinconfig"
        
        # Export necessary vars
        # Note: VAULT_ROLE_ID, VAULT_SECRET_ID, DEPLOY_ENV and CONFIG_SERVER_URL are exported
        export APP_NAME="${REPO_NAME}"
        export MS_NAME="${REPO_NAME}"

        # Check necessary vars
        [ -z "${CONFIG_SERVER_URL}" ] && { echo "Not defined CONFIG_SERVER_URL var"; return 1; } || export CONFIG_SERVER_URL
        [ -z "${VAULT_ROLE_ID}"     ] && { echo "Not defined VAULT_ROLE_ID var"; return 1; }
        [ -z "${VAULT_SECRET_ID}"   ] && { echo "Not defined VAULT_SECRET_ID var"; return 1; }

        # Use allinconfig loader
        berglas exec python3 /usr/local/app/app.py 
        [ $? -ne 0 ] && return 1

        # Check file
        [ ! -f "${ENV_FILE_OUT:-allinconfig.env}" ] && { echo "Not found file ${ENV_FILE_OUT:-allinconfig.env}"; return 1; }

        # Include in session the environment variables created in previous step
        if [ -z "$FILE_OUT_FORMAT" ]; then
            . ${ENV_FILE_OUT:-allinconfig.env}
        fi

        # Configure substitutions with allinconfig values
        while read line; do
            var=$(echo "${line}"   | sed -r "s/export ([A-Z_]*)=(.*)/\1/"); 
            value=$(echo "${line}" | sed -r "s/export ([A-Z_]*)=(.*)/\2/"); 
            [ -z "${subs_allinconfig}" ] && subs_allinconfig=",_${var}=${value}" || subs_allinconfig="${subs_allinconfig},_${var}=${value}"
        done < ${ENV_FILE_OUT:-allinconfig.env}
        
        # Delete quotes
        subs_allinconfig=$(echo ${subs_allinconfig} | sed 's/"//g')
    else
        echo "Not found configuration repository, not use allinconfig"
    fi

    return 0
}