# FootballHub – Lernnotizen

Diese Notizen dokumentieren die Konzepte, die ich beim Aufbau von FootballHub gelernt und praktisch angewendet habe.

Das Projekt ist bewusst praxisorientiert und KI-unterstützt entwickelt. Mein Ziel ist dabei, die Architektur und Infrastruktur, die ich einsetze, auch selbst zu verstehen.

## 1. REST API

### GET und POST

`GET /teams` liest die vorhandenen Teams.

`POST /teams` sendet Daten an das Backend, um ein neues Team anzulegen.

### Pfadparameter

Bei einem Endpoint wie `GET /teams/{team_id}` ist ein Teil der URL variabel.

Zum Beispiel:

`GET /teams/11`

übergibt die `11` als `team_id` an das Backend.

### Datenvalidierung

Das Pydantic-Modell `TeamCreate` legt fest, welche Felder beim Erstellen eines Teams erwartet werden und welche Datentypen diese haben sollen.

### Persistenz

Die aktuellen Teamdaten werden nur im Arbeitsspeicher des laufenden Python-Prozesses gespeichert.

Teams, die während der Laufzeit hinzugefügt werden, verschwinden daher nach einem Neustart der Anwendung. Eine Datenbank soll später für eine dauerhafte Speicherung sorgen.

---

## 2. Docker

Docker verpackt eine Anwendung zusammen mit ihrer Laufzeitumgebung und ihren Abhängigkeiten.

Dadurch sollen unter anderem Situationen vermieden werden, in denen eine Anwendung auf einem Rechner funktioniert, auf einem anderen aufgrund einer unterschiedlichen Umgebung aber nicht.

### Image und Container

Ein Docker Image ist die Vorlage, aus der Container erstellt werden.

Ein Container ist eine laufende Instanz eines Images.

Der grundlegende Ablauf ist:

`Dockerfile → Image → Container → FastAPI`

### Port-Mapping

Die FastAPI-Anwendung läuft innerhalb des Containers auf Port 8000.

Mit:

`docker run -p 8000:8000 footballhub-backend`

wird ein Port meines Rechners auf den Port des Containers weitergeleitet. Dadurch kann ich die Anwendung von meinem Rechner aus erreichen.

---

## 3. Kubernetes

Die aktuelle Struktur meiner Anwendung lässt sich vereinfacht so darstellen:

`Docker Image → Deployment → ReplicaSet → Pod → Container → FastAPI`

### Pod

Ein Pod ist die kleinste Ausführungseinheit, die Kubernetes verwaltet.

Bei FootballHub enthält ein Pod aktuell einen Container, in dem das FastAPI-Backend läuft.

### Deployment

Ein Deployment beschreibt den gewünschten Zustand der Anwendung.

Zum Beispiel bedeutet:

`replicas: 3`

dass Kubernetes dafür sorgen soll, dass drei FootballHub-Pods vorhanden sind.

### Desired State und Self-Healing

Ich habe einen laufenden FootballHub-Pod manuell gelöscht.

Kubernetes hat automatisch einen neuen Pod erzeugt, weil im Deployment weiterhin die gewünschte Anzahl an Replikaten festgelegt war.

Kubernetes hat dabei nicht den gelöschten Pod repariert. Stattdessen wurde ein neuer Pod erstellt, um den gewünschten Zustand wiederherzustellen.

### Service

Pods sind austauschbar und ihre IP-Adressen können sich ändern.

Ein Service bietet deshalb einen stabilen Zugriffspunkt und leitet Anfragen an die passenden Pods weiter.

Bei drei Replikaten hatte mein FootballHub-Service beispielsweise drei Pod-Endpunkte:

- `10.244.0.8:8000`
- `10.244.0.9:8000`
- `10.244.0.10:8000`

Dadurch können mehrere Instanzen des Backends hinter demselben Service erreichbar sein, ohne dass ein Client die einzelnen Pod-Adressen kennen muss.

### Skalierung

Ich habe im Deployment:

`replicas: 1`

auf:

`replicas: 3`

geändert.

Kubernetes hat daraufhin drei FootballHub-Pods bereitgestellt.

Wenn einer dieser Pods verschwindet, erzeugt Kubernetes einen Ersatz, da weiterhin drei Replikate als gewünschter Zustand definiert sind.

### Versionierte Images und Rolling Updates

Image-Tags wie `v1` und `v2` machen unterschiedliche Versionen einer Anwendung eindeutig unterscheidbar.

Dadurch ist besser nachvollziehbar, welche Version gerade verwendet wird und zu welcher älteren Version gegebenenfalls zurückgekehrt werden kann.

Ein Kubernetes Deployment kann Pods mit einer alten Version schrittweise durch Pods mit einer neuen Version ersetzen. Dies wird als Rolling Update bezeichnet.

Dadurch kann die Anwendung während eines Updates grundsätzlich weiter verfügbar bleiben.

---

## 4. Bisheriges Troubleshooting

### ErrImageNeverPull

Mein erstes Kubernetes Deployment ist mit:

`ErrImageNeverPull`

fehlgeschlagen.

Über:

`kubectl get pods`

konnte ich erkennen, dass der Pod nicht erfolgreich gestartet wurde.

Anschließend habe ich mit:

`kubectl describe pod <pod-name>`

weitere Informationen abgerufen.

Im Bereich `Events` war zu erkennen, dass Kubernetes das Image `footballhub-backend:latest` nicht finden konnte, während `imagePullPolicy` auf `Never` gesetzt war.

Dadurch konnte Kubernetes das benötigte Image weder lokal verwenden noch herunterladen.

### Port bereits belegt

Beim Einsatz von `kubectl port-forward` waren die lokalen Ports 8000 und später 8080 bereits durch andere Prozesse belegt.

Mit einem anderen lokalen Port konnte ich den Service trotzdem erreichbar machen:

`kubectl port-forward service/footballhub-backend 8081:8000`

Dabei ist `8081` der Port auf meinem Rechner und `8000` der Port des Kubernetes-Service.