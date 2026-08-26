"""OpenTelemetry 初始化。

开发环境默认用 ConsoleSpanExporter：span 树直接打印到控制台，零外部依赖。
设置 OTEL_EXPORTER_OTLP_ENDPOINT（如 http://localhost:4318）后自动切换
OTLP HTTP 导出，可对接 Jaeger / OpenTelemetry Collector。

初始化前 get_tracer() 返回 NoOpTracer（span 不产生任何副作用），
因此测试环境不初始化也完全安全——现有测试不受影响。
"""

import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

TRACER_NAME = "merchantops-agent"


def setup_tracing() -> None:
    provider = TracerProvider()

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)
