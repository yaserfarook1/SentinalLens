"""
Custom Exception Classes
"""


class SentinelLensException(Exception):
    """Base exception for SentinelLens"""
    pass


class KqlParseException(SentinelLensException):
    """KQL parsing failed"""
    pass


class AzureApiException(SentinelLensException):
    """Azure API call failed"""
    pass


class CostCalculationException(SentinelLensException):
    """Cost calculation failed"""
    pass


class AuthenticationException(SentinelLensException):
    """Authentication/authorization failed"""
    pass


class ReportGenerationException(SentinelLensException):
    """Report generation failed"""
    pass
