function get_configuration_allinconfig {

    subs_allinconfig=""

    # Check configuration repository
    #git ls-remote "https://${GITHUB_USER}:${GITHUB_TOKEN}@${REPO_URL#https://}-config.git" &> /dev/null
    curl -s --user "${GITHUB_USER}:${GITHUB_TOKEN}" "https://api.github.com/repos/${ORG_NAME}/${REPO_NAME}-config/branches" | jq '.[] | .name' 2> /dev/null | grep -wq "master"

    if [ $? -eq 0 ]; then

        echo "Getting configuration of allinconfig"
        
        # Export necessary vars
        export APP_NAME=${REPO_NAME}
        export MS_NAME=${REPO_NAME}
        #export VAULT_ROLE_ID=2f1c7b7e-f0e6-b423-ac39-1eaf55175b29
        #export VAULT_SECRET_ID=cdd63512-d25e-bb77-2557-47c0d1e66c54
        #export VAULT_ROLE_ID="berglas://gcp-services-pre-eslm-berglas-secrets/allinconfig-role-id"
        #export VAULT_SECRET_ID="berglas://gcp-services-pre-eslm-berglas-secrets/allinconfig-secret-id"

        export DEPLOY_ENV=pre
        export CONFIG_SERVER_URL='http://allinconfig--server-dev.support-prev-eslm.tech.adeo.cloud'

        ROLE_ID=$(berglas access gcp-services-pre-eslm-berglas-secrets/allinconfig-role-id 2>&1)
        echo "ROLE_ID = $ROLE_ID"

        SECRET_ID=$(berglas access gcp-services-pre-eslm-berglas-secrets/allinconfig-secret-id 2>&1)
        echo "SECRET_ID = $SECRET_ID"

        berglas access gcp-services-pre-eslm-berglas-secrets/allinconfig-secret-id

        # Check necessary vars
        [ -z "${VAULT_ROLE_ID}"   ] && { echo "Not defined VAULT_ROLE_ID var"; return 1; }
        [ -z "${VAULT_SECRET_ID}" ] && { echo "Not defined VAULT_SECRET_ID var"; return 1; }

        # Use allinconfig loader
        #python3 /usr/local/app/app.py 
        berglas exec python3 /usr/local/app/app.py 
        [ $? -ne 0 ] && return 1

        # TO DO: INCLUIR LA COMPROBACION DEL COMANDO app.py Y SI EXISTE EL FICHERO allinconfig.env

        # Include in session the environment variables created in previous step
        if [ -z "$FILE_OUT_FORMAT" ]; then
            . ${ENV_FILE_OUT:-allinconfig.env}
        fi

        # Check file
        [ ! -f "${ENV_FILE_OUT}" ] && { echo "Not found file ${ENV_FILE_OUT}"; return 1; }

        # Configure substitutions with allinconfig values
        while read line; do
            var=$(echo $line   | sed -r "s/export ([A-Z_]*)=(.*)/\1/"); 
            value=$(echo $line | sed -r "s/export ([A-Z_]*)=(.*)/\2/"); 
            [ -z "$subs_allinconfig" ] && subs_allinconfig=",_${var}=${value}" || subs_allinconfig="${subs_allinconfig},_${var}=${value}"
        done < ${ENV_FILE_OUT}
        #done < allinconfig.env
        
        # Delete quotes
        subs_allinconfig=$(echo ${subs_allinconfig} | sed 's/"//g')
    else
        echo "Not found configuration repository, continue"
    fi

    #return "${subs_allinconfig}"
    return 0
}