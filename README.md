How to run:
- Use `docker compose up` to start the services. You'll find the following:
    - localhost:3000 - Grafana
    - localhost:8080 - Custom Python API
    - localhost:8081 - Prometheus UI
- Access the Python API Swagger Docs using `localhost:8080/docs`
- Send some test requests
- Access Grafana UI at localhost:3000`
- Select "Explore" and choose the predefined "Prometheus" data source
- Query metrics using the Grafana UI

ToDo:
- [ ] Send Prometheus Logs using Alloy
- [ ] Add another API to show scalability?