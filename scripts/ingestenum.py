import random

try:
    from com.xhaus.jyson import JysonCodec as json
except ImportError:
    import json
from abstract_thread import AbstractThread, generate_job_range
from abstract_thread import generate_metrics_tenants


class EnumIngestThread(AbstractThread):
    # The list of metric numbers for all threads in this worker
    metrics = []

    @staticmethod
    def _create_metrics(agent_number, config):
        """ Generate all the metrics for this worker

        The metrics are a list of batches.  Each batch is a list of metrics
        processed by a single metrics ingest request.
        """
        metrics = generate_metrics_tenants(
            config['enum_num_tenants'],
            config['enum_metrics_per_tenant'],
            agent_number,
            config['num_nodes'],
            EnumIngestThread.generate_metrics_for_tenant)

        return EnumIngestThread.divide_metrics_into_batches(
            metrics,
            config['batch_size'])

    @classmethod
    def num_threads(cls, config):
        return config['enum_ingest_weight']

    @staticmethod
    def generate_metrics_for_tenant(tenant_id, metrics_per_tenant):
        l = []
        for x in range(metrics_per_tenant):
            l.append([tenant_id, x])
        return l

    @staticmethod
    def divide_metrics_into_batches(metrics, batch_size):
        b = []
        for i in range(0, len(metrics), batch_size):
            b.append(metrics[i:i + batch_size])
        return b

    # TODO: Add enum prefix to config
    @staticmethod
    def generate_enum_metric_name(metric_id, config):
        return "enum_grinder_" + config['name_fmt'] % metric_id

    def __init__(self, thread_num, agent_num, request, config):
        AbstractThread.__init__(self, thread_num, agent_num, request, config)

    def generate_enum_suffix(self):
        return "_" + str(random.randint(0, self.config['enum_num_values']))

    def generate_enum_metric(self, time, tenant_id, metric_id):
        return {'tenantId': str(tenant_id),
                'timestamp': time,
                'enums': [{'name': self.generate_enum_metric_name(metric_id,
                                                                  self.config),
                           'value': 'e_g_' + str(
                               metric_id) + self.generate_enum_suffix()}]
                }

    def generate_payload(self, time, tenant_metric_id_pairs):
        payload = [self.generate_enum_metric(time, pair[0], pair[1])
                   for pair in tenant_metric_id_pairs]
        return json.dumps(payload)

    def ingest_url(self):
        return "%s/v2.0/tenantId/ingest/aggregated/multi" % self.config[
            'url']

    def make_request(self, logger, time, tenant_metric_id_pairs=None):
        if tenant_metric_id_pairs is None:
            tenant_metric_id_pairs = []
            for i in xrange(self.config['batch_size']):
                tenant_id = random.randint(1, self.config['enum_num_tenants'])
                metric_id = random.randint(1, self.config['enum_metrics_per_tenant'])
                pair = [tenant_id, metric_id]
                tenant_metric_id_pairs.append(pair)
        payload = self.generate_payload(time, tenant_metric_id_pairs)
        result = self.request.POST(self.ingest_url(), payload)
        return result
