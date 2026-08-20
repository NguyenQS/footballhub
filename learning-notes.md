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

### Fehlgeschlagenes Deployment und Rollback

Ich habe absichtlich ein nicht vorhandenes Image `footballhub-backend:v999` deployt.

Mit `kubectl get pods` erkannte ich zunächst `ErrImagePull` und später `ImagePullBackOff`.

Mit `kubectl describe pod` konnte ich in den Events sehen, dass Kubernetes das Image nicht herunterladen konnte.

Während des fehlgeschlagenen Rolling Updates liefen die bisherigen funktionierenden Pods weiter.

Mit `kubectl rollout undo deployment/footballhub-backend` konnte ich zur vorherigen funktionierenden Version zurückkehren.

Wichtig ist, anschließend auch die lokale Deployment-YAML wieder auf die funktionierende Version zu setzen, da ein Rollback im Cluster die lokale Konfigurationsdatei nicht automatisch verändert.

### CrashLoopBackOff

Ich habe absichtlich einen Fehler eingebaut, durch den die FastAPI-Anwendung beim Start abgestürzt ist.

Das Image konnte erfolgreich geladen werden und der Container wurde gestartet. Die Anwendung ist jedoch sofort mit Exit Code 1 beendet worden.

Kubernetes hat den Container mehrfach neu gestartet. Da bei jedem Start derselbe Anwendungsfehler auftrat, entstand ein CrashLoopBackOff.

Mit `kubectl logs <pod-name>` konnte ich die eigentliche Python-Fehlermeldung sehen.

`kubectl describe pod <pod-name>` zeigte dagegen den Kubernetes-Zustand, unter anderem Restart Count, Exit Code und BackOff-Events.

Self-Healing kann einen reproduzierbaren Fehler im Anwendungscode nicht reparieren. Kubernetes kann den Container nur erneut starten oder eine funktionierende Version deployen.

### Readiness und Liveness

Ein laufender Container ist nicht automatisch bereit, Traffic zu bearbeiten.

Die Readiness Probe prüft, ob ein Pod aktuell Anfragen über den Service bekommen soll. Wenn die Readiness Probe fehlschlägt, kann der Container weiterlaufen, wird aber nicht als Ready betrachtet.

Die Liveness Probe prüft, ob die Anwendung noch gesund genug ist, um weiterzulaufen. Wenn sie wiederholt fehlschlägt, kann Kubernetes den Container neu starten.

Ich habe die Readiness Probe absichtlich auf einen nicht vorhandenen Endpoint gesetzt. Der Pod war weiterhin `Running`, aber nur `0/1 Ready`. Das Rolling Update konnte dadurch nicht abgeschlossen werden.

Nach dem Zurücksetzen des Pfads auf `/health` wurden wieder alle drei Pods `1/1 Ready`.

### Ressourcen und Namespaces

Requests geben an, mit welchem Ressourcenbedarf Kubernetes beim Scheduling eines Containers rechnen soll. Limits begrenzen, wie viele Ressourcen ein Container maximal verwenden darf.

Für FootballHub habe ich Requests und Limits für CPU und Arbeitsspeicher definiert.

Namespaces ermöglichen eine logische Trennung von Kubernetes-Ressourcen innerhalb eines Clusters. Ich habe FootballHub aus dem `default`-Namespace in einen eigenen Namespace `footballhub-dev` überführt.

Dabei habe ich gesehen, dass Ressourcen nicht einfach zwischen Namespaces verschoben werden. Stattdessen wurden zunächst neue Ressourcen im neuen Namespace erstellt. Die alten Ressourcen im `default`-Namespace musste ich anschließend gezielt entfernen.

Ohne Angabe von `-n` verwendet `kubectl` standardmäßig den `default`-Namespace. Mit `-A` können Ressourcen über alle Namespaces hinweg angezeigt werden.

### Ingress

Ein Service stellt einen stabilen Zugriffspunkt für die Pods einer Anwendung bereit.

Ein Ingress kann HTTP-/HTTPS-Anfragen anhand von Hosts oder Pfaden an unterschiedliche Services weiterleiten. Dadurch können mehrere Anwendungen über einen gemeinsamen externen Einstiegspunkt erreichbar gemacht werden.

In meiner lokalen Kubernetes-Umgebung ist aktuell kein Ingress Controller installiert. Daher habe ich die Ingress-Ressource für FootballHub konfiguriert, aber nicht praktisch über einen Ingress Controller betrieben.

Für lokales Testen und Debugging habe ich bisher `kubectl port-forward` verwendet.

### GitOps mit Flux

Flux läuft im Kubernetes-Cluster und überwacht den gewünschten Zustand aus Git.

Ich habe die Anzahl der Replikate in `deployment.yaml` von 3 auf 2 geändert und nur einen Git-Push ausgeführt. Ohne `kubectl apply` hat Flux die Änderung erkannt und automatisch einen Pod beendet, sodass der Cluster wieder dem in Git beschriebenen Zustand entsprach.

Dadurch wird Git zur zentralen Quelle für den gewünschten Cluster-Zustand.