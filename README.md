# mesos-poller
Webservice for probing every instance of a webservice running in a Mesos/Marathon cluster

## Purpose

* Webservices can be started in multible instances running in the Mesos cluster.

* To test every instance, the Mesos configuration is probed for information about the number of instances and their target endpoint.
Each instance is then probed in parallel, and the HTTP status is collected. Information about the success/failure of the probing is returned.
