# Blueflood Grinder Integration
##Intro
Grinder is a distributed load testing tool described [here](http://grinder.sourceforge.net/g3/getting-started.html)

This code defines implementations of grinder worker threads meant to repeatedly invoke the required number of BF api calls during each "reporting interval"

It also includes the infrastructure to divide the total work described in the grinder properties file across all the workers in the distributed system.

##Architecture
The BF grinder system is designed to take a single properties file that lists the total number of threads to be used to generate load, and allocate each of those threads to generate a certain kind of http request.

The BF grinder code creates different types of threads to handle the different kinds of requests
to be generated.  Currently the thread types are:

* IngestThread - create requests for the  "/ingest/multi" endpoint
* AnnotationsIngestThread - ingests to the "events" endpoint
* Various query threads:
  * SinglePlotQuery - send GET requests to `<tenant>/views/<metric>` with `from`, `to`, and `resolution` params
  * MultiPlotQuery - send POST requests to `<tenant>/views` with `from`, `to`, and `resolution` params
  * SearchQuery - send requests to `<tenant>/metrics/search`
  * AnnotationsQuery - send requests to `<tenant>/events/getEvents` with `from`, `until` params

The `grinder.threads` property determines the number of threads started by each worker process.
How those threads are divided up between the different `*Thread` classes is determined by _weight_ properties.
A given thread type will be created for a number of threads proportional to the weight specified for that thread type divided by the total weight for all thread types.

Each thread will continuously generate HTTP requests of the specified type for as long as Grinder is configured to run.

### Properties that control operation

Grinder-specific properties are discussed in more detail [here](http://grinder.sourceforge.net/g3/properties.html)

* `grinder.runs` - The number of times the grinder script should be run. If `0`, then it will run indefinitely, until manually stopped. Default is `1`.
* `grinder.processes` - The number of worker processes started by each agent. Default is `1`.
* `grinder.threads` - The number of threads per worker process. Default is `1`.
* `[grinder.bf.]url` - The HTTP Url for ingestion-based traffic. Default is `http://localhost:19000`.
* `[grinder.bf.]query_url` - The HTTP Url for query-based traffic. Default is `http://localhost:20000`.
* `[grinder.bf.]max_multiplot_metrics` - Default is `10`.
* `[grinder.bf.]name_fmt` - Default is `org.example.metric.%d`.

* `[grinder.bf.]throttling_group.<name>.max_requests_per_minute` - Create a throttling group with the given `name`. The value of the property is taken as the throttling group's `max_requests_per_minute` parameter. By default, no throttling groups are created if no properties are specified.

* `[grinder.bf.]ingest_weight` - Default is `15`.
* `[grinder.bf.]ingest_num_tenants` - Ingestion threads randomly generate a numerical tenant id in the range of `[0,ingest_num_tenants)`. Change this property to control how many different tenant id's are used when sending standard metrics to the service. Default is `4`.
* `[grinder.bf.]ingest_metrics_per_tenant` - Ingestion threads randomly generate a numerical metric name suffix in the range of `[0,ingest_metrics_per_tenant)`. Metric names will generally be of the form `org.example.metric.%d`, or whatever the `name_fmt` property is set to. Change this property to control how many different metrics will have data generated for them. Default is `15`.
* `[grinder.bf.]ingest_batch_size` - Ingestion threads will generate this many metrics in a single payload (HTTP request body). Default is `5`.
* `[grinder.bf.]ingest_delay_millis` - Configures delayed metrics. Default is `""`, which doesn't produced any delayed metrics.
* `[grinder.bf.]ingest_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `IngestThread` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]annotations_weight` - Default is `5`.
* `[grinder.bf.]annotations_num_tenants` - Exactly like `ingest_num_tenants`, except that this property controls the number of tenant id's for the `AnnotationsIngestThread` class. This property is provided so that ingest and annotation ingest threads can be configured independently. Default is `5`.
* `[grinder.bf.]annotations_per_tenant` - Exactly like `ingest_metrics_per_tenant`, except that this property controls the number of metric name suffixes for the `AnnotationsIngestThread` class. This property is provided so that ingest threads can be configured independently. Default is `10`.
* `[grinder.bf.]annotations_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `AnnotationsIngestThread` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]singleplot_query_weight` - Default is `10`.
* `[grinder.bf.]singleplot_query_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `SinglePlotQuery` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]multiplot_query_weight` - Default is `10`.
* `[grinder.bf.]multiplot_query_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `MultiPlotQuery` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]search_query_weight` - Default is `10`.
* `[grinder.bf.]search_query_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `SearchQuery` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]annotations_query_weight` - Default is `8`.
* `[grinder.bf.]annotations_query_throttling_group` - Name of an above-defined throttling group. The named tgroup will be assigned to all `AnnotationsQuery` objects. Default is `None`. If the tgroup name is blank, or is not defined amongh the throttling groups (or if there is a _spelling_error_), then no throttling will be performed for this thread type.

* `[grinder.bf.]auth_url` - URL to use to authenticate against before running the perf test. Should be the url to an OpenStack compatible identity service.
* `[grinder.bf.]auth_username` - The username to authenticate with before running the perf test.
* `[grinder.bf.]auth_api_key` - The API key to authenticate with before running the perf test.
* `[grinder.bf.]auth_properties_path` - Path to a `.properties` file that contains the user credentials. If any of `auth_url`, `auth_username`, or `auth_api_key` is not specified in the main config file, then this property will be checked for credentials. The property file referred to by this property will **only** be checked for user credentials; any other properties defined in it will not be used for any purpose, nor will this `.properties` file in any way override the main config.
* `[grinder.bf.]auth_properties_encr_key_file` - Path to a `.properties` file that hass a `password` entry giving a simple encryption key. If this property is specified, then properties in the `auth_properties_path` file can be encrypted using jasypt, e.g. `ENC(abc123...)`. The property file referred to by `auth_properties_encr_key_file` will **only** be checked for a `password` property; any other properties defined in it will not be used for any purpose, nor will this property file in any way override the main config.

##Installing
The following command will download the necessary software packages and place them under the `dependencies/` folder:

```bash
./setup-dependencies.sh
```

Note this needs to be run on each node in the cluster, as well as the console.

##Starting the console
The GUI is started like so:
```bash
cd $BLUEFLOOD_INSTALL/contrib/grinder
java -cp  resources/grinder-3.11/lib/grinder.jar:resources/jyson-1.0.2/lib/jyson-1.0.2.jar net.grinder.Console
```
The console can be run headless, like so:
```bash
java -cp  resources/grinder-3.11/lib/grinder.jar:resources/jyson-1.0.2/lib/jyson-1.0.2.jar net.grinder.Console -headless
```

and you interact with a rest api like so:
```bash
curl -X POST http://localhost:6373/agents/stop-workers
curl -X POST http://localhost:6373/agents/start-workers
```
The graphical console gives some useful status info, so you may prefer using that.


##Starting the agents
Each agent is started like so:
```bash
java -cp  resources/grinder-3.11/lib/grinder.jar:resources/jyson-1.0.2/lib/jyson-1.0.2.jar net.grinder.Grinder $GRINDER_PROPERTIES_FILE
```
There are currently some example properties files here:
```bash
$BLUEFLOOD_INSTALL/contrib/grinder/properties/
```

grinder.properties runs the unit tests
grinder.properties.local has some configs for running on your localhost
grinder.properties.staging runs the staging configuration and is meant to be run on two nodes

##Coverage
There is a set of unit tests to check the function of the individual components in the scripts.
The relevant file is `scripts/tests.py`.
To run the unit tests under Jython and Grinder, you can simply run `./run-unit-tests.sh` at the bash prompt.
Alternately, there is a `./run-unit-tests-with-coverage.sh` command that will run the unit tests under Python, collect code coverage numbers, and produce a report at `htmlcov/index.html`.
