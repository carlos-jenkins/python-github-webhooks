from webhooks import application


def main():
    application.config['APPLICATION_ROOT'] = '/github-webhook'
    application.config['application_root'] = '/github-webhook'
    application.register_prefix['APPLICATION_ROOT'] = '/github-webhook'
    application.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
