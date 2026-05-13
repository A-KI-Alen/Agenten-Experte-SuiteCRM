# SuiteCRM Topic Map

Diese Topic Map ist das Routing-Werkzeug fuer CEO und Collector.

| Topic | Pages | Activation terms |
| --- | ---: | --- |
| `admin_configuration` | 52 | admin panel, configuration, modules, users, roles, system settings |
| `async_schedulers` | 9 | cron, schedulers, Symfony Messenger, async task workers, background jobs |
| `developer_api` | 13 | API v4.1/v8, JSON API, Postman setup, API errors |
| `developer_extensions` | 47 | custom code, backend/frontend extensions, vardefs, process API, architecture |
| `email_calendar` | 28 | inbound/outbound email, OAuth mail provider, calendar sync, Microsoft/Google |
| `general` | 102 | general SuiteCRM docs and uncategorized topics |
| `installation_operations` | 33 | install, webserver, compatibility, performance, environment setup |
| `search_elasticsearch` | 14 | Elasticsearch setup, indexing, search troubleshooting |
| `security_auth` | 25 | OAuth, SAML, LDAP, login throttling, sessions, trusted hosts |
| `troubleshooting` | 15 | errors, logs, failed upgrade, diagnostics, support |
| `upgrade_migration` | 63 | version upgrade, 7.x to 8.x migration, release changes, manual migration tasks |
| `user_guides` | 80 | end-user workflows and UI usage |

## Escalation Flow

1. Debugger arbeitet zwei echte Runs autonom.
2. Wenn nicht geloest: Debugger uebergibt komprimierte Lage an CEO.
3. CEO waehlt passende Programmspezialisten ueber diese Topic Map.
4. Spezialist antwortet nur lesend nach `answer_contract` aus `profile.toml`.
5. Collector fuehrt Expertenantworten und Debug-Kontext zusammen.
6. Debugger setzt den Fix direkt um und testet.
