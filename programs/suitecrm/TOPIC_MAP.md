# SuiteCRM Topic Map

Diese Topic Map ist das Routing-Werkzeug fuer CEO und Collector.

| Topic | Pages | Activation terms |
| --- | ---: | --- |
| `admin_configuration` | 31 | admin panel, configuration, modules, users, roles, system settings |
| `async_schedulers` | 6 | cron, schedulers, Symfony Messenger, async task workers, background jobs |
| `developer_api` | 12 | API v4.1/v8, JSON API, Postman setup, API errors |
| `developer_extensions` | 40 | custom code, backend/frontend extensions, vardefs, process API, architecture |
| `email_calendar` | 16 | inbound/outbound email, OAuth mail provider, calendar sync, Microsoft/Google |
| `general` | 79 | general SuiteCRM docs and uncategorized topics |
| `installation_operations` | 21 | install, webserver, compatibility, performance, environment setup |
| `search_elasticsearch` | 12 | Elasticsearch setup, indexing, search troubleshooting |
| `security_auth` | 16 | OAuth, SAML, LDAP, login throttling, sessions, trusted hosts |
| `troubleshooting` | 11 | errors, logs, failed upgrade, diagnostics, support |
| `upgrade_migration` | 50 | version upgrade, 7.x to 8.x migration, release changes, manual migration tasks |
| `user_guides` | 60 | end-user workflows and UI usage |

## Escalation Flow

1. Debugger arbeitet zwei echte Runs autonom.
2. Wenn nicht geloest: Debugger uebergibt komprimierte Lage an CEO.
3. CEO waehlt passende Programmspezialisten ueber diese Topic Map.
4. Spezialist antwortet nur lesend nach `answer_contract` aus `profile.toml`.
5. Collector fuehrt Expertenantworten und Debug-Kontext zusammen.
6. Debugger setzt den Fix direkt um und testet.
