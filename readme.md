###  OpenShift EFK  - external setup 
This repo describes available options and required steps for 
connecting OpenShift EFK stack to external ES and Kibana instances.

## Option 1 - Connect FluentD instances to ex external stand alone (not OCP based) ES and Kibana setup
- Download and extract ES and Kibana
    ES: https://www.elastic.co/downloads/past-releases/elasticsearch-5-6-13
    Kibana: https://www.elastic.co/downloads/past-releases/kibana-5-6-13
- Extract the archives and start ES & Kibana
    `cd elasticsearch && ./bin/elasticsearch`
    `cd kibana && ./bin/kibana`
- Import Indexes and Indexes patters into ES instance    
     - The `es-imoprter.py` script import indexes and indexes pattern into external EFK setup. 
    The import script uses following JSON source files
    - index_templates.json 
    - index_pattern.json
    - index_patterns_names.json
    
    ##### Usage 
    `python es-importer.py [ES_HOST_IP] [ES_PORT]`
    
    #####  Data source 
    The indexes and indexes patters was exported directly from running ES pod. 
    Execute following command to re-export the data again
    - Export index templates:  `curl -s -X GET --cacert /etc/elasticsearch/secret/admin-ca --cert /etc/elasticsearch/secret/admin-cert --key /etc/elasticsearch/secret/admin-key https://localhost:9200/_template`
    - Export index patterns: The index patterns template could be found official [GitHub](https://github.com/openshift/origin-aggregated-logging) repo, [here](https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/elasticsearch/index_patterns/com.redhat.viaq-openshift.index-pattern.json)
    - Export index patterns names: Could be either from running Kibana UI or 
    by parsing the `index_templates` files. 
    As from now we have following patterns names: 
    `[".operations.*", ".all",".orphaned.*","project.*"]`
- Update FluentD `daemonet` with `oc edit daemonsets logging-fluentd` and set 
    `ES_HOST`, `ES_PORT`, `OPS_HOST`, and `OPS_PORT` to point to IP of the external ES instance. More details [here](https://docs.openshift.com/container-platform/3.11/install_config/aggregate_logging.html#sending-logs-to-an-external-elasticsearch-instance)
- Update FluentD `daemonet` with `oc edit daemonsets logging-fluentd` and set image to the following value: `image: docker.io/dimssss/ose-logging-fluentd:v3.11.83`. To build your own FluentD image, take a look on custom-fluetd folder in that repo.
 

## Option 2 - Connect FluentD instances to external EFK which is running inside other OpenShift cluster
- Deploy EFK on both OpenShift clusters. (as for example I'll call it external and internal, internal OCP will exports logs to EFK which is runs on external OCP) by running following command.     
    ```bash
    cd /usr/share/ansible/openshift-ansible
    ansible-playbook playbooks/openshift-logging/config.yml 
    ```
- Make sure everything is up and running 
    ```bash
    userx:~ λ oc get pods -n openshift-logging
    NAME                                      READY     STATUS    RESTARTS   AGE
    logging-es-data-master-2nghl23v-1-77bbm   2/2       Running   0          20m
    logging-fluentd-9nztq                     1/1       Running   0          22m
    logging-fluentd-hn94z                     1/1       Running   1          2d
    logging-fluentd-n2tsz                     1/1       Running   1          2d
    logging-fluentd-s9rtg                     1/1       Running   1          2d
    logging-kibana-ops-1-kxzcx                2/2       Running   4          3d
    ```
- Export FluentD certificates from external cluster and use them in internal cluster
    Export from external: `oc get secrets logging-fluentd -o yaml -n openshift-logging`
    Edit `logging-fluentd` secret in internal cluster and update the `ca` `cert` `key` and `ops-ca` `ops-cert` `ops-key` with the values from external cluster.

- To allow FluentD instances to connect to external cluster expose ES instance of external cluster by creating a route
    ```yaml
    apiVersion: route.openshift.io/v1
    kind: Route
    metadata:
      name: logging-es
      namespace: openshift-logging
    spec:
      host: logging-es-openshift-logging.router.default.svc.cluster.local
      tls:
        termination: passthrough
      to:
        kind: Service
        name: logging-es
        weight: 100
    ```
- Test the exposed route by running following command: `curl -k -s -X GET --cacert admin-ca --cert admin-cert --key admin-key https://logging-es-openshift-logging.router.default.svc.cluster.local/_template`
    the `admin-ca`  `admin-cert` and `admin-key` could be retrieved from `logging-elasticsearch` secret. 

- Update FluentD `daemonet` with `oc edit daemonsets logging-fluentd` and set `ES_HOST`, `ES_PORT`, `OPS_HOST`, and `OPS_PORT` more details [here](https://docs.openshift.com/container-platform/3.11/install_config/aggregate_logging.html#sending-logs-to-an-external-elasticsearch-instance)

- Open Kibana dashboard and test the results


