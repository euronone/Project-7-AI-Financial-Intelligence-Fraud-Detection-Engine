"""CloudWatch metrics and logging integration."""

import logging
import time
from typing import Any, Callable

import boto3
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CloudWatchHandler(logging.Handler):
    """Custom logging handler for CloudWatch."""

    def __init__(self):
        super().__init__()
        self.cloudwatch = boto3.client("logs", region_name=settings.AWS_REGION)
        self.log_group = f"/ecs/finshield-{settings.APP_ENV}"
        self.log_stream = f"{settings.APP_ENV}-{settings.INSTANCE_ID}"

    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to CloudWatch."""
        try:
            msg = self.format(record)
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        "timestamp": int(time.time() * 1000),
                        "message": msg,
                    }
                ],
            )
        except Exception as e:
            self.handleError(record)
            print(f"Error sending to CloudWatch: {e}")


class CloudWatchMetrics:
    """CloudWatch metrics publisher."""

    def __init__(self):
        self.cloudwatch = boto3.client("cloudwatch", region_name=settings.AWS_REGION)
        self.namespace = "FinShield"

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: dict | None = None,
    ) -> None:
        """Put a metric to CloudWatch."""
        try:
            kwargs = {
                "Namespace": self.namespace,
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
            }

            if dimensions:
                kwargs["Dimensions"] = [
                    {"Name": k, "Value": str(v)} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(**kwargs)
        except Exception as e:
            print(f"Error publishing metric {metric_name}: {e}")

    def record_fraud_detection(
        self, fraud_score: float, decision: str, fraud_category: str
    ) -> None:
        """Record fraud detection metrics."""
        self.put_metric(
            "FraudDetectionCount",
            1,
            dimensions={
                "Decision": decision,
                "Category": fraud_category,
            },
        )
        self.put_metric(
            "FraudScore",
            fraud_score,
            unit="None",
            dimensions={"Decision": decision},
        )

    def record_api_latency(self, endpoint: str, latency_ms: float) -> None:
        """Record API latency."""
        self.put_metric(
            "APILatency",
            latency_ms,
            unit="Milliseconds",
            dimensions={"Endpoint": endpoint},
        )

    def record_model_inference_time(self, model_name: str, time_ms: float) -> None:
        """Record model inference time."""
        self.put_metric(
            "ModelInferenceTime",
            time_ms,
            unit="Milliseconds",
            dimensions={"Model": model_name},
        )

    def record_db_query_time(self, query_type: str, time_ms: float) -> None:
        """Record database query time."""
        self.put_metric(
            "DBQueryTime",
            time_ms,
            unit="Milliseconds",
            dimensions={"QueryType": query_type},
        )

    def record_error(self, error_type: str, endpoint: str) -> None:
        """Record API errors."""
        self.put_metric(
            "APIErrorCount",
            1,
            dimensions={
                "ErrorType": error_type,
                "Endpoint": endpoint,
            },
        )


def setup_logging(app_name: str = "finshield") -> logging.Logger:
    """Configure structured logging with CloudWatch integration."""
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG if settings.APP_ENV == "development" else logging.INFO)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    json_formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # CloudWatch handler (only in production)
    if settings.APP_ENV != "development":
        try:
            cloudwatch_handler = CloudWatchHandler()
            cloudwatch_handler.setLevel(logging.INFO)
            cloudwatch_handler.setFormatter(json_formatter)
            logger.addHandler(cloudwatch_handler)
        except Exception as e:
            logger.warning(f"Failed to setup CloudWatch logging: {e}")

    return logger


# Global instances
logger = setup_logging()
metrics = CloudWatchMetrics()


def track_metric(metric_name: str, unit: str = "None"):
    """Decorator to track custom metrics."""

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                metrics.put_metric(
                    metric_name,
                    elapsed_ms,
                    unit="Milliseconds",
                )
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                metrics.put_metric(
                    metric_name,
                    elapsed_ms,
                    unit="Milliseconds",
                )
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise

        # Determine if async or sync
        if hasattr(func, "__await__"):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
