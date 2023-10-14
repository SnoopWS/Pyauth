# 🚀 PyAuth (Python Auth) 🚀

Tired of using keyauth or reaps? Look no further! PyAuth is your go-to authentication solution. It's faster, better, and more scalable than keyauth. It can process queries in milliseconds. 😎

## 🌟 Features:

- 🆔 UUID apps
- 🔑 License key management (delete, add, edit time)
- 🔒 Assign HWID (SSID) to license keys
- 📋 List all license keys
- 🔑 Key Validation
- 📅 License expiry
- 📄 License pages
- 👤 Username assigning
- 📅 Plan assigning to keys

## 🚀 API Endpoints:

### Add an application and assign it to a username (GET)

[https://YOURSERVERIP/add_application?admin_key={ADMIN_KEY}&secret_key={SECRET_KEY}&username={USERNAME}](#)

### List all license keys per page and their info in JSON (GET)

[https://YOURSERVERIP/list_user_license_keys?username={USERNAME}&admin_key={ADMIN_KEY}&page=1](#)

### Delete a license key (GET)

[https://YOURSERVERIP/delete_license_key/{application}?application={UUID}&admin_key={YOURADMINKEY}&username={USERNAME}&license_key={LICENSE_KEY}](#)

### List all license keys bypassing the secret_key (Admin) (GET)

[https://YOURSERVERIP/admin/license_keys/{application}?application={UUID}&admin_key={YOURADMINKEY}](#)

### Add an application (GET)

[https://YOURSERVERIP/admin_key={YOURADMINKEY}&secret_key={SECRET_KEY}&username={USERNAME}](#)

### List all license keys in a specific application (GET)

[https://YOURSERVERIP/list_application_license_keys?username={USERNAME}&admin_key={ADMIN_KEY}&application={UUID}](#)

### Add a license key (clients) (POST)

[https://YOURSERVERIP/secret/add_license_key?application={UUID}&secret_key={SECRET_KEY}&plan={PLAN}&expiry_day={EXPIRY_DAYS}](#)

### List all client's keys using your secret_key (POST)

[https://YOURSERVERIP/license_keys/{application}?application={UUID}&secret_key={IDFK}](#)

### Main endpoint for verifying keys (POST)

[https://YOURSERVERIP/license_keys/{application}/apiv1?application={UUID}&license_key={LICENSE_KEY}&hwid={SSID_FORMAT}](#)

### Assign an HWID (POST)

[https://YOURSERVERIP/license_keys/{application}/assign_hwid?application={UUID}&license_key={LICENSE_KEY}&hwid={SSID_FORMAT}](#)

Feel free to use this enhanced README to make your project stand out on GitHub. 😃 If you have any questions or need further assistance, let us know! 🌟
