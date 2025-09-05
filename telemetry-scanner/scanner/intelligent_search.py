"""
Intelligent Multi-Modal Search System with domain-specific knowledge and advanced ranking.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import re
from .code_graph_manager import code_graph_manager

@dataclass
class TelemetryInfrastructure:
    """Analysis of existing telemetry infrastructure in the codebase."""
    instrumentation_libraries: Dict[str, Dict[str, Any]]
    configuration_files: List[Path]
    existing_spans: List[str]
    available_attributes: List[str]
    gaps: List[str]
    recommendations: List[str]

@dataclass
class ConfigurationOption:
    """Represents a configuration option for an instrumentation library."""
    library: str
    option_name: str
    option_value: Any
    description: str
    solves_problems: List[str]

class SearchStrategy(Enum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    PATTERN = "pattern"
    KEYWORD = "keyword"
    GRAPH_BASED = "graph_based"

class RelevanceScore(Enum):
    EXACT_MATCH = 100
    HIGH = 85
    MEDIUM = 70
    LOW = 50
    MINIMAL = 25


@dataclass
class SearchResult:
    file_path: Path
    strategy: SearchStrategy
    relevance_score: int
    reasoning: str
    matching_patterns: List[str]
    context_snippets: List[str]
    confidence: float

@dataclass
class DomainKnowledge:
    """Domain-specific knowledge for C# and OpenTelemetry."""
    telemetry_patterns: Dict[str, List[str]]
    csharp_patterns: Dict[str, List[str]]
    architectural_patterns: Dict[str, List[str]]
    semantic_relationships: Dict[str, List[str]]

class IntelligentSearchEngine:
    """Advanced search engine with domain knowledge and multi-modal search."""
    
    def __init__(self, repo_path: Path, code_graph_path: Optional[Path] = None):
        # Ensure repo_path is a Path object
        self.repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        self.code_graph_path = code_graph_path
        print(f"[DEBUG] IntelligentSearchEngine.__init__: Initializing with repo_path={self.repo_path}, code_graph_path={code_graph_path}")
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.domain_knowledge = self._load_domain_knowledge()  # Load domain knowledge first
        self.telemetry_configs = self._load_telemetry_configuration_knowledge()
        self.file_index = self._build_file_index()  # Then build file index (needs domain knowledge)
        
        # Use shared code graph manager
        self.code_graph_data = None
        if code_graph_path:
            print(f"[DEBUG] IntelligentSearchEngine.__init__: Loading code graph data from {code_graph_path}")
            self.code_graph_data = code_graph_manager.get_graph_data(str(code_graph_path))
            self.code_graph = self.code_graph_data.raw_data if self.code_graph_data else None
            if self.code_graph_data:
                print(f"[DEBUG] IntelligentSearchEngine.__init__: Code graph loaded successfully")
            else:
                print(f"[DEBUG] IntelligentSearchEngine.__init__: Failed to load code graph")
        else:
            print(f"[DEBUG] IntelligentSearchEngine.__init__: No code graph path provided")
            self.code_graph = None
        # --- domain-aware booster knobs (safe defaults) ---
        self.signal_boost_enabled = True
        self.signal_boost_cap = 30                     # max total bonus per file
        self.signal_boost_require_existing_signal = True  # only boost files that already show some OT/target-domain hints
        self.signal_boost_log = False                  # set True to print per-file boosts

        
    def _load_domain_knowledge(self) -> DomainKnowledge:
        """Load domain-specific knowledge patterns."""
        return DomainKnowledge(
            telemetry_patterns={
                "instrumentation": [
                    "AddOpenTelemetry", "AddHttpClientInstrumentation", "AddSqlClientInstrumentation",
                    "AddRabbitMQInstrumentation", "ActivitySource", "Meter", "ActivityListener",
                    "SetTag", "SetAttribute", "StartActivity", "CreateActivity"
                ],
                "configuration": [
                    "TracerProviderBuilder", "MeterProviderBuilder", "OpenTelemetryBuilder",
                    "WithTracing", "WithMetrics", "WithLogging", "AddConsoleExporter",
                    "AddJaegerExporter", "AddOtlpExporter"
                ],
                "attributes": [
                    "http.method", "http.url", "db.statement", "messaging.system",
                    "service.name", "service.version", "deployment.environment"
                ],
                "spans": [
                    "Activity", "IActivity", "ActivityContext", "ActivityKind",
                    "ActivityStatusCode", "ActivityTagsCollection"
                ]
            },
            csharp_patterns={
                "dependency_injection": [
                    "IServiceCollection", "ServiceCollectionExtensions", "AddScoped",
                    "AddSingleton", "AddTransient", "ConfigureServices"
                ],
                "middleware": [
                    "IMiddleware", "MiddlewareExtensions", "UseMiddleware", "app.Use",
                    "RequestDelegate", "HttpContext"
                ],
                "configuration": [
                    "IConfiguration", "IOptions", "IConfigurationBuilder", "appsettings",
                    "ConfigurationManager", "IHostBuilder"
                ],
                "startup": [
                    "Startup", "Program", "Main", "CreateHostBuilder", "ConfigureServices",
                    "Configure", "WebApplication"
                ]
            },
            architectural_patterns={
                "factory": ["Factory", "Create", "Builder", "IFactory"],
                "repository": ["Repository", "IRepository", "DataAccess", "Store"],
                "service": ["Service", "IService", "Handler", "Manager"],
                "controller": ["Controller", "ApiController", "ControllerBase"]
            },
            semantic_relationships={
                "telemetry": ["observability", "monitoring", "tracing", "metrics", "logging"],
                "instrumentation": ["measurement", "tracking", "recording", "collection"],
                "configuration": ["setup", "initialization", "bootstrap", "registration"],
                "middleware": ["pipeline", "filter", "interceptor", "handler"]
            }
        )
    
    def _load_telemetry_configuration_knowledge(self) -> Dict[str, List[ConfigurationOption]]:
        """Load knowledge base of telemetry configuration options."""
        return {
            "SqlClientInstrumentation": [
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="EnableConnectionLevelAttributes",
                    option_value=True,
                    description="Enables database name and server attributes",
                    solves_problems=["missing db.name", "database identification", "connection tracking"]
                ),
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="SetDbStatementForText",
                    option_value=True,
                    description="Enables SQL statement text and operation name",
                    solves_problems=["missing db.operation", "sql query tracking", "stored procedure names"]
                ),
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="SetDbStatementForStoredProcedure",
                    option_value=True,
                    description="Enables recording stored procedure names",
                    solves_problems=["missing stored procedure names", "db.operation for sprocs"]
                ),
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records SQL exceptions as span events",
                    solves_problems=["missing error tracking", "sql exceptions", "database errors"]
                ),
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="Filter",
                    option_value="Func<string, object, bool>",
                    description="Filter which database operations to instrument",
                    solves_problems=["too much noise", "selective instrumentation", "performance optimization"]
                ),
                ConfigurationOption(
                    library="SqlClientInstrumentation",
                    option_name="Enrich",
                    option_value="Action<Activity, string, object>",
                    description="Add custom attributes to database spans",
                    solves_problems=["missing custom attributes", "business context", "enrichment"]
                )
            ],
            "HttpClientInstrumentation": [
                ConfigurationOption(
                    library="HttpClientInstrumentation",
                    option_name="FilterHttpRequestMessage",
                    option_value="Func<HttpRequestMessage, bool>",
                    description="Filter which HTTP requests to instrument",
                    solves_problems=["too much noise", "selective instrumentation", "health checks"]
                ),
                ConfigurationOption(
                    library="HttpClientInstrumentation",
                    option_name="EnrichWithHttpRequestMessage",
                    option_value="Action<Activity, HttpRequestMessage>",
                    description="Add custom attributes from HTTP request",
                    solves_problems=["missing request headers", "custom enrichment", "business context"]
                ),
                ConfigurationOption(
                    library="HttpClientInstrumentation",
                    option_name="EnrichWithHttpResponseMessage",
                    option_value="Action<Activity, HttpResponseMessage>",
                    description="Add custom attributes from HTTP response",
                    solves_problems=["missing response headers", "custom enrichment", "response analysis"]
                ),
                ConfigurationOption(
                    library="HttpClientInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records HTTP exceptions as span events",
                    solves_problems=["missing http errors", "exception tracking"]
                )
            ],
            "AspNetCoreInstrumentation": [
                ConfigurationOption(
                    library="AspNetCoreInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records ASP.NET Core exceptions",
                    solves_problems=["missing exception tracking", "web errors"]
                ),
                ConfigurationOption(
                    library="AspNetCoreInstrumentation",
                    option_name="Filter",
                    option_value="Func<HttpContext, bool>",
                    description="Filter which HTTP requests to instrument",
                    solves_problems=["health check noise", "selective instrumentation", "performance"]
                ),
                ConfigurationOption(
                    library="AspNetCoreInstrumentation",
                    option_name="EnrichWithHttpRequest",
                    option_value="Action<Activity, HttpRequest>",
                    description="Add custom attributes from HTTP request",
                    solves_problems=["missing request context", "user info", "custom headers"]
                ),
                ConfigurationOption(
                    library="AspNetCoreInstrumentation",
                    option_name="EnrichWithHttpResponse",
                    option_value="Action<Activity, HttpResponse>",
                    description="Add custom attributes from HTTP response",
                    solves_problems=["missing response context", "status details", "custom headers"]
                ),
                ConfigurationOption(
                    library="AspNetCoreInstrumentation",
                    option_name="EnableGrpcAspNetCoreSupport",
                    option_value=True,
                    description="Enables gRPC support for ASP.NET Core",
                    solves_problems=["missing grpc traces", "grpc instrumentation"]
                )
            ],
            "GrpcNetClientInstrumentation": [
                ConfigurationOption(
                    library="GrpcNetClientInstrumentation",
                    option_name="SuppressDownstreamInstrumentation",
                    option_value=True,
                    description="Suppresses HttpClient instrumentation for gRPC calls",
                    solves_problems=["duplicate spans", "grpc http noise"]
                ),
                ConfigurationOption(
                    library="GrpcNetClientInstrumentation", 
                    option_name="EnrichWithHttpRequestMessage",
                    option_value="Action<Activity, HttpRequestMessage>",
                    description="Add custom attributes to gRPC client spans",
                    solves_problems=["missing grpc context", "custom enrichment"]
                )
            ],
            "EntityFrameworkCoreInstrumentation": [
                ConfigurationOption(
                    library="EntityFrameworkCoreInstrumentation",
                    option_name="SetDbStatementForText",
                    option_value=True,
                    description="Records the EF Core generated SQL",
                    solves_problems=["missing sql queries", "ef core visibility", "db.statement"]
                ),
                ConfigurationOption(
                    library="EntityFrameworkCoreInstrumentation",
                    option_name="Filter",
                    option_value="Func<string, object, bool>",
                    description="Filter which EF operations to instrument",
                    solves_problems=["too much ef noise", "selective instrumentation"]
                ),
                ConfigurationOption(
                    library="EntityFrameworkCoreInstrumentation",
                    option_name="Enrich",
                    option_value="Action<Activity, string, object>",
                    description="Add custom attributes to EF Core spans",
                    solves_problems=["missing ef context", "custom enrichment"]
                )
            ],
            "RedisInstrumentation": [
                ConfigurationOption(
                    library="RedisInstrumentation",
                    option_name="SetVerboseDatabaseStatements",
                    option_value=True,
                    description="Records Redis command arguments",
                    solves_problems=["missing redis commands", "redis visibility", "db.statement"]
                ),
                ConfigurationOption(
                    library="RedisInstrumentation",
                    option_name="FlushInterval",
                    option_value="TimeSpan.FromSeconds(1)",
                    description="Interval for flushing Redis activities",
                    solves_problems=["redis performance", "batching optimization"]
                ),
                ConfigurationOption(
                    library="RedisInstrumentation",
                    option_name="Enrich",
                    option_value="Action<Activity, IProfiledCommand>",
                    description="Add custom attributes to Redis spans",
                    solves_problems=["missing redis context", "custom enrichment"]
                )
            ],
            "MassTransitInstrumentation": [
                ConfigurationOption(
                    library="MassTransitInstrumentation",
                    option_name="Filter",
                    option_value="Func<ConsumeContext, bool>",
                    description="Filter which message operations to instrument",
                    solves_problems=["message noise", "selective instrumentation"]
                )
            ],
            "NServiceBusInstrumentation": [
                ConfigurationOption(
                    library="NServiceBusInstrumentation",
                    option_name="CaptureMessageBody",
                    option_value=True,
                    description="Captures message body content",
                    solves_problems=["missing message content", "message debugging"]
                )
            ],
            "QuartzInstrumentation": [
                ConfigurationOption(
                    library="QuartzInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records Quartz job exceptions",
                    solves_problems=["missing job errors", "quartz exceptions"]
                )
            ],
            "HangfireInstrumentation": [
                ConfigurationOption(
                    library="HangfireInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records Hangfire job exceptions", 
                    solves_problems=["missing job errors", "hangfire exceptions"]
                )
            ],
            "ElasticsearchInstrumentation": [
                ConfigurationOption(
                    library="ElasticsearchInstrumentation",
                    option_name="SuppressDownstreamInstrumentation",
                    option_value=True,
                    description="Suppresses HttpClient instrumentation for Elasticsearch",
                    solves_problems=["duplicate spans", "elasticsearch http noise"]
                ),
                ConfigurationOption(
                    library="ElasticsearchInstrumentation",
                    option_name="ParseAndFormatRequest",
                    option_value=True,
                    description="Parses and formats Elasticsearch requests",
                    solves_problems=["missing elasticsearch queries", "db.statement"]
                )
            ],
            "MongoDBInstrumentation": [
                ConfigurationOption(
                    library="MongoDBInstrumentation",
                    option_name="CaptureCommandText",
                    option_value=True,
                    description="Captures MongoDB command text",
                    solves_problems=["missing mongo queries", "db.statement", "mongo visibility"]
                )
            ],
            "MySqlDataInstrumentation": [
                ConfigurationOption(
                    library="MySqlDataInstrumentation", 
                    option_name="SetDbStatementForText",
                    option_value=True,
                    description="Records MySQL command text",
                    solves_problems=["missing mysql queries", "db.statement", "mysql visibility"]
                ),
                ConfigurationOption(
                    library="MySqlDataInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records MySQL exceptions",
                    solves_problems=["missing mysql errors", "database exceptions"]
                )
            ],
            "NpgsqlInstrumentation": [
                ConfigurationOption(
                    library="NpgsqlInstrumentation",
                    option_name="SetDbStatementForText", 
                    option_value=True,
                    description="Records PostgreSQL command text",
                    solves_problems=["missing postgresql queries", "db.statement", "postgres visibility"]
                ),
                ConfigurationOption(
                    library="NpgsqlInstrumentation",
                    option_name="RecordException",
                    option_value=True,
                    description="Records PostgreSQL exceptions",
                    solves_problems=["missing postgres errors", "database exceptions"]
                )
            ],
            "OracleInstrumentation": [
                ConfigurationOption(
                    library="OracleInstrumentation",
                    option_name="SetDbStatementForText",
                    option_value=True,
                    description="Records Oracle command text",
                    solves_problems=["missing oracle queries", "db.statement", "oracle visibility"]
                )
            ],
            "CassandraInstrumentation": [
                ConfigurationOption(
                    library="CassandraInstrumentation",
                    option_name="SetDbStatementForText",
                    option_value=True,
                    description="Records Cassandra CQL statements",
                    solves_problems=["missing cassandra queries", "db.statement", "cql visibility"]
                )
            ],
            "AWSInstrumentation": [
                ConfigurationOption(
                    library="AWSInstrumentation",
                    option_name="SuppressDownstreamInstrumentation",
                    option_value=True,
                    description="Suppresses HttpClient instrumentation for AWS SDK",
                    solves_problems=["duplicate spans", "aws http noise"]
                ),
                ConfigurationOption(
                    library="AWSInstrumentation",
                    option_name="AddLegacyAWSClientSupport",
                    option_value=True,
                    description="Adds support for legacy AWS SDK versions",
                    solves_problems=["legacy aws sdk", "older aws versions"]
                )
            ],
            "StackExchangeRedisInstrumentation": [
                ConfigurationOption(
                    library="StackExchangeRedisInstrumentation",
                    option_name="SetVerboseDatabaseStatements",
                    option_value=True,
                    description="Records Redis command details",
                    solves_problems=["missing redis commands", "db.statement", "redis debugging"]
                ),
                ConfigurationOption(
                    library="StackExchangeRedisInstrumentation",
                    option_name="FlushInterval",
                    option_value="TimeSpan.FromSeconds(1)",
                    description="Controls batching of Redis activities",
                    solves_problems=["redis performance", "activity batching"]
                )
            ]
        }
    
    def analyze_telemetry_infrastructure(self) -> TelemetryInfrastructure:
        """Analyze existing telemetry infrastructure in the codebase."""
        instrumentation_libs = {}
        config_files = []
        
        # Find telemetry configuration files
        for file_path, file_info in self.file_index.items():
            content = file_info["content"]
            
            # Check if this file configures telemetry
            if any(pattern in content for pattern in self.domain_knowledge.telemetry_patterns["configuration"]):
                config_files.append(Path(file_path))
                
                # Extract instrumentation libraries being used
                for pattern in self.domain_knowledge.telemetry_patterns["instrumentation"]:
                    if pattern in content:
                        lib_name = self._extract_library_name(pattern, content)
                        if lib_name:
                            instrumentation_libs[lib_name] = self._analyze_library_config(lib_name, content)
        
        return TelemetryInfrastructure(
            instrumentation_libraries=instrumentation_libs,
            configuration_files=config_files,
            existing_spans=self._extract_existing_spans(),
            available_attributes=self._extract_available_attributes(),
            gaps=[],  # Will be filled by gap analysis
            recommendations=[]  # Will be filled by recommendation engine
        )
    
    def _extract_library_name(self, pattern: str, content: str) -> Optional[str]:
        """Extract instrumentation library name from pattern using intelligence."""
        # Get available library names from our knowledge base
        available_libraries = list(self.telemetry_configs.keys())
        
        # Use intelligent matching instead of hardcoded rules
        for lib_name in available_libraries:
            # Extract the core component name (e.g., "SqlClient" from "SqlClientInstrumentation")
            core_name = lib_name.replace("Instrumentation", "")
            
            # Check if pattern matches this library
            if core_name.lower() in pattern.lower():
                return lib_name
        
        # Fallback: check if pattern contains any library name directly
        for lib_name in available_libraries:
            if lib_name.lower() in pattern.lower():
                return lib_name
                
        return None
    
    def _analyze_library_config(self, lib_name: str, content: str) -> Dict[str, Any]:
        """Analyze the configuration of a specific instrumentation library using intelligent detection."""
        config = {
            "configured_options": [],
            "available_options": self.telemetry_configs.get(lib_name, []),
            "missing_options": []
        }
        
        # Intelligent option detection instead of simple string matching
        for option in config["available_options"]:
            if self._is_option_configured(option, content, lib_name):
                config["configured_options"].append(option.option_name)
            else:
                config["missing_options"].append(option)
        
        return config
    
    def _is_option_configured(self, option: ConfigurationOption, content: str, lib_name: str) -> bool:
        """Intelligently detect if a configuration option is already set."""
        # Look for the specific option name
        if option.option_name in content:
            return True
        
        # Look for the option in the context of the library configuration
        method_name = f"Add{lib_name}"
        if method_name in content:
            # Find the configuration block and check if the option is set there
            import re
            pattern = rf'{re.escape(method_name)}\s*\([^)]*\)\s*=>\s*\{{([^}}]*)}}'
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if option.option_name in match:
                    return True
        
        return False
    
    def suggest_configuration_solution(self, problem_description: str, infrastructure: TelemetryInfrastructure) -> Optional[str]:
        """Suggest configuration-based solutions using intelligent problem matching."""
        problem_lower = problem_description.lower()
        
        best_match = None
        best_score = 0
        
        # Check each instrumentation library for applicable solutions
        for lib_name, lib_config in infrastructure.instrumentation_libraries.items():
            for missing_option in lib_config["missing_options"]:
                # Calculate relevance score using intelligent matching
                score = self._calculate_problem_solution_relevance(problem_lower, missing_option)
                
                if score > best_score and score > 0.3:  # Minimum relevance threshold
                    best_score = score
                    best_match = (lib_name, missing_option)
        
        if best_match:
            lib_name, option = best_match
            return self._generate_config_solution(lib_name, option)
        
        return None
    
    def _calculate_problem_solution_relevance(self, problem: str, option: ConfigurationOption) -> float:
        """Calculate how well a configuration option solves the described problem."""
        score = 0.0
        
        # Direct keyword matching
        problem_keywords = set(problem.split())
        for solution_keyword in option.solves_problems:
            solution_words = set(solution_keyword.lower().split())
            common_words = problem_keywords.intersection(solution_words)
            if common_words:
                score += len(common_words) / len(solution_words)
        
        # Semantic similarity for key terms
        key_terms = {
            'database': ['db', 'sql', 'query', 'connection'],
            'http': ['request', 'response', 'client', 'web'],
            'exception': ['error', 'failure', 'exception'],
            'operation': ['operation', 'command', 'action'],
            'name': ['name', 'identifier', 'identity']
        }
        
        for category, terms in key_terms.items():
            if any(term in problem for term in terms):
                if any(term in ' '.join(option.solves_problems) for term in terms):
                    score += 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_config_solution(self, lib_name: str, option: ConfigurationOption) -> str:
        """Generate configuration solution code using intelligent templating."""
        # Determine the method name pattern
        method_name = f"Add{lib_name}"
        
        # Generate appropriate value representation
        if isinstance(option.option_value, bool):
            value_str = str(option.option_value).lower()
        elif isinstance(option.option_value, str) and option.option_value.startswith(("Func<", "Action<", "TimeSpan")):
            value_str = option.option_value  # Keep complex types as-is
        else:
            value_str = str(option.option_value)
        
        # Generate the configuration code
        return f"""// {option.description}
options.{method_name}(o =>
{{
    o.{option.option_name} = {value_str};
}});"""
    
    def _extract_existing_spans(self) -> List[str]:
        """Extract existing span names from the codebase."""
        spans = []
        for file_path, file_info in self.file_index.items():
            content = file_info["content"]
            # Look for Activity.StartActivity calls
            import re
            span_matches = re.findall(r'StartActivity\s*\(\s*["\']([^"\']+)["\']', content)
            spans.extend(span_matches)
        return list(set(spans))
    
    def _extract_available_attributes(self) -> List[str]:
        """Extract attributes that are currently being set."""
        attributes = []
        for file_path, file_info in self.file_index.items():
            content = file_info["content"]
            # Look for SetTag calls
            import re
            attr_matches = re.findall(r'SetTag\s*\(\s*["\']([^"\']+)["\']', content)
            attributes.extend(attr_matches)
        return list(set(attributes))
    
    def _build_file_index(self) -> Dict[str, Dict]:
        """
        Build an index of all C# files with metadata.
        
        UNIVERSAL IMPROVEMENT: Filter out irrelevant files that clutter search results.
        """
        index = {}
        
        for cs_file in self.repo_path.rglob("*.cs"):
            if cs_file.stat().st_size == 0:
                continue
            
            # UNIVERSAL IMPROVEMENT: Filter out irrelevant files
            if self._should_exclude_file(cs_file):
                continue
                
            try:
                content = cs_file.read_text(encoding="utf-8", errors="ignore")
                
                index[str(cs_file)] = {
                    "path": cs_file,
                    "content": content,
                    "size": cs_file.stat().st_size,
                    "keywords": self._extract_keywords(content),
                    "patterns": self._identify_patterns(content),
                    "imports": self._extract_imports(content),
                    "classes": self._extract_classes(content),
                    "methods": self._extract_methods(content)
                }
            except Exception as e:
                print(f"Warning: Could not index file {cs_file}: {e}")
        
        return index
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """
        UNIVERSAL IMPROVEMENT: Determine if a file should be excluded from search.
        
        WHY: Auto-generated files, build artifacts, and dependencies clutter results
        and are never the right place to add telemetry instrumentation.
        
        BEFORE: ATL-86508 found 12/15 AssemblyInfo.cs files (all irrelevant)
        AFTER: Filters out irrelevant files, focuses on actual business logic
        """
        
        file_str = file_path.as_posix().lower()
        file_name = file_path.name.lower()
        
        # Universal irrelevant patterns for all repositories
        irrelevant_patterns = [
            # Build artifacts
            "/obj/", "/bin/", "/debug/", "/release/", 
            "/packages/", "/node_modules/",
            
            # Auto-generated files
            ".assemblyinfo.cs", ".assemblyattributes.cs",
            ".globalassemblyinfo.cs", "temporarygeneratedfile",
            ".designer.cs", ".g.cs", ".g.i.cs",
            
            # Migration and scaffold files (often auto-generated)
            "migration", "scaffold", ".migration.cs",
            
            # Test files (unless specifically searching for test patterns)
            ".test.cs", ".tests.cs", "test/", "tests/",
            
            # Reference and example files
            "/reference/", "/examples/", "/sample/", "/demo/",
            
            # Third-party dependencies
            "/vendor/", "/lib/", "/libs/", "/packages/",
            
            # Backup and temporary files
            ".bak", ".tmp", ".temp", "~"
        ]
        
        # Check if file matches any irrelevant pattern
        for pattern in irrelevant_patterns:
            if pattern in file_str:
                return True
        
        # Additional check for auto-generated file content
        if file_name.endswith(".cs"):
            try:
                # Quick check for auto-generated markers
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_lines = f.read(1000)  # Read first 1KB
                    auto_generated_markers = [
                        "auto-generated", "autogenerated", "code generated",
                        "<autogenerated />", "this code was generated",
                        "// <auto-generated>", "/* auto-generated */"
                    ]
                    if any(marker in first_lines.lower() for marker in auto_generated_markers):
                        return True
            except:
                pass  # If we can't read the file, don't exclude it
        
        return False
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract meaningful keywords from code content."""
        # Extract class names, method names, and important identifiers
        keywords = []
        
        # Extract class declarations
        class_matches = re.findall(r'class\s+(\w+)', content)
        keywords.extend(class_matches)
        
        # Extract interface declarations
        interface_matches = re.findall(r'interface\s+(\w+)', content)
        keywords.extend(interface_matches)
        
        # Extract method declarations
        method_matches = re.findall(r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:\w+\s+)?(\w+)\s*\(', content)
        keywords.extend(method_matches)
        
        # Extract using statements
        using_matches = re.findall(r'using\s+([^;]+);', content)
        keywords.extend([u.strip() for u in using_matches])
        
        return list(set(keywords))
    
    def _identify_patterns(self, content: str) -> List[str]:
        """Identify domain-specific patterns in code."""
        patterns = []
        
        # Check telemetry patterns
        for category, pattern_list in self.domain_knowledge.telemetry_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"telemetry.{category}.{pattern}")
        
        # Check C# patterns
        for category, pattern_list in self.domain_knowledge.csharp_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"csharp.{category}.{pattern}")
        
        # Check architectural patterns
        for category, pattern_list in self.domain_knowledge.architectural_patterns.items():
            for pattern in pattern_list:
                if pattern in content:
                    patterns.append(f"architecture.{category}.{pattern}")
        
        return patterns
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract using/import statements."""
        imports = []
        using_matches = re.findall(r'using\s+([^;]+);', content)
        for match in using_matches:
            imports.append(match.strip())
        return imports
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class and interface names."""
        classes = []
        
        # Extract class declarations
        class_matches = re.findall(r'(?:public|internal|private)?\s*(?:static|abstract|sealed)?\s*class\s+(\w+)', content)
        classes.extend(class_matches)
        
        # Extract interface declarations
        interface_matches = re.findall(r'(?:public|internal|private)?\s*interface\s+(\w+)', content)
        classes.extend(interface_matches)
        
        return classes
    
    def _extract_methods(self, content: str) -> List[str]:
        """Extract method names."""
        methods = []
        method_matches = re.findall(
            r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:virtual\s+)?(?:override\s+)?(?:\w+\s+)?(\w+)\s*\(',
            content
        )
        methods.extend(method_matches)
        return methods
    
    def multi_modal_search(self, intent: Dict, top_k: int = 30) -> List[SearchResult]:
        """
        Perform intent-driven multi-modal search using all available strategies.
        
        NEW APPROACH: Configuration-first, then custom code.
        Analyze existing telemetry infrastructure before suggesting custom solutions.
        """
        all_results = []
        
        # UNIVERSAL IMPROVEMENT 1: Infrastructure Analysis First
        infrastructure = self.analyze_telemetry_infrastructure()
        config_solution = self.suggest_configuration_solution(intent.get("description", ""), infrastructure)
        
        if config_solution:
            # If we have a configuration solution, prioritize telemetry config files
            all_results.extend(self._find_telemetry_configuration_files(top_k // 2))
            
            # Add metadata about the suggested solution
            for result in all_results[:5]:  # Top 3 results get the config suggestion
                result.reasoning = f"Configuration solution available: {config_solution[:100]}..."
                result.relevance_score += 20  # Boost relevance
        
        # Strategy 1: Direct Method/Class Search (HIGHEST PRIORITY)
        direct_results = self._direct_code_search(intent, top_k // 3)
        all_results.extend(direct_results)
        
        # Strategy 2: Telemetry Infrastructure Discovery (HIGH PRIORITY)
        infrastructure_results = self._telemetry_infrastructure_search(intent, top_k // 4)
        all_results.extend(infrastructure_results)
        
        # Strategy 3: Structural Search (based on static analysis query)
        if intent.get("static_analysis_query"):
            structural_results = self._structural_search(intent, top_k // 4)
            all_results.extend(structural_results)
        
        # Strategy 4: Pattern-Based Search
        pattern_results = self._pattern_search(intent, top_k // 4)
        all_results.extend(pattern_results)
        
        # Strategy 5: Keyword Search
        keyword_results = self._keyword_search(intent, top_k // 4)
        all_results.extend(keyword_results)
        
        # Strategy 6: Semantic Search (FALLBACK ONLY)
        if len(all_results) < top_k // 2:
            semantic_results = self._semantic_search(intent, top_k // 2)
            all_results.extend(semantic_results)
        
        # Strategy 7: Graph-Based Search (if code graph available)
        if self.code_graph:
            graph_results = self._graph_based_search(intent, top_k // 4)
            all_results.extend(graph_results)
        
        # Consolidate and rank results
        consolidated_results = self._consolidate_results(all_results)
        
        # Apply domain-specific ranking
        ranked_results = self._apply_domain_ranking(consolidated_results, intent)
        
        return ranked_results[:top_k]

    
    def _semantic_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Perform semantic search with domain knowledge enhancement."""
        query = intent.get("semantic_description", "")
        if not query:
            return []
        
        # Enhance query with domain-specific terms
        enhanced_query = self._enhance_query_with_domain_knowledge(query, intent)
        
        # Get file contents for embedding
        file_paths = list(self.file_index.keys())
        file_contents = [self.file_index[path]["content"] for path in file_paths]
        
        if not file_contents:
            return []
        
        # Generate embeddings
        query_embedding = self.model.encode([enhanced_query])
        file_embeddings = self.model.encode(file_contents)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, file_embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            file_path = Path(file_paths[idx])
            similarity_score = similarities[idx]
            
            # Convert similarity to relevance score
            relevance_score = int(similarity_score * 100)
            
            # Extract context snippets
            context_snippets = self._extract_context_snippets(
                self.file_index[file_paths[idx]]["content"], enhanced_query
            )
            
            result = SearchResult(
                file_path=file_path,
                strategy=SearchStrategy.SEMANTIC,
                relevance_score=relevance_score,
                reasoning=f"Semantic similarity: {similarity_score:.3f}",
                matching_patterns=[],
                context_snippets=context_snippets,
                confidence=similarity_score
            )
            results.append(result)
        
        return results
    
    def _enhance_query_with_domain_knowledge(self, query: str, intent: Dict) -> str:
        """Enhance search query with domain-specific knowledge."""
        enhanced_terms = [query]
        
        # Add semantic relationships
        for key, related_terms in self.domain_knowledge.semantic_relationships.items():
            if key.lower() in query.lower():
                enhanced_terms.extend(related_terms)
        
        # Add operation-specific terms
        telemetry_op = intent.get("telemetry_operation", {})
        op_type = telemetry_op.get("type", "")
        op_action = telemetry_op.get("action", "")
        
        if op_type in self.domain_knowledge.telemetry_patterns:
            enhanced_terms.extend(self.domain_knowledge.telemetry_patterns[op_type])
        
        if op_action == "CREATE":
            enhanced_terms.extend(["new", "initialize", "setup"])
        elif op_action == "ADD_ATTRIBUTES":
            enhanced_terms.extend(["SetTag", "SetAttribute", "enrich"])
        
        return " ".join(enhanced_terms)
    
    def _direct_code_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """
        UNIVERSAL IMPROVEMENT: Direct search for specific method calls, classes, or patterns.
        
        WHY: Instead of relying on semantic similarity, we directly search for the exact 
        code elements mentioned in the intent. This works for any telemetry scenario:
        - Database: ExecuteStoredProcedure, DbCommand
        - HTTP: HttpClient, HttpRequest
        - Messaging: SendMessage, PublishEvent
        - Logging: LogEvent, WriteLog
        
        BEFORE: Would miss exact matches because semantic search is fuzzy
        AFTER: Guarantees we find the exact code the intent is targeting
        """
        results = []
        
        # Get direct search targets from intent
        static_query = intent.get("static_analysis_query", {})
        search_targets = []
        
        # Add method calls
        if static_query.get("find_method_call"):
            search_targets.append(static_query["find_method_call"])
        
        # Add class names
        if static_query.get("find_class"):
            search_targets.append(static_query["find_class"])
        
        # Add any specific keywords from intent
        search_keywords = intent.get("search_keywords", [])
        search_targets.extend(search_keywords)
        
        # Perform direct grep-style search for each target
        for target in search_targets:
            if not target:
                continue
                
            for file_path, file_data in self.file_index.items():
                content = file_data["content"]
                
                # Count exact matches
                exact_matches = len(re.findall(re.escape(target), content, re.IGNORECASE))
                
                if exact_matches > 0:
                    # Extract method context if this is a method call
                    context_snippets = self._extract_method_context(content, target)
                    
                    # High relevance for exact matches
                    relevance_score = RelevanceScore.EXACT_MATCH.value
                    if exact_matches > 1:
                        relevance_score = min(100, relevance_score + (exact_matches - 1) * 5)
                    
                    result = SearchResult(
                        file_path=Path(file_path),
                        strategy=SearchStrategy.KEYWORD,
                        relevance_score=relevance_score,
                        reasoning=f"Direct match for '{target}' ({exact_matches} occurrences)",
                        matching_patterns=[target],
                        context_snippets=context_snippets,
                        confidence=0.95
                    )
                    results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _telemetry_infrastructure_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """
        UNIVERSAL IMPROVEMENT: Find existing telemetry infrastructure that can be enhanced.
        
        WHY: Instead of creating parallel telemetry systems, we find existing ones to extend.
        This works universally by looking for common telemetry patterns:
        - OpenTelemetry: Activity, ActivitySource, SetTag
        - Custom telemetry: Instrumentation, Tracing, Monitoring
        - Configuration: Startup, Program, Extensions
        
        BEFORE: Would propose new telemetry systems alongside existing ones
        AFTER: Finds existing infrastructure and suggests enhancing it
        """
        results = []
        
        # Universal telemetry patterns to search for
        telemetry_patterns = [
            # OpenTelemetry patterns
            "ActivitySource", "Activity.SetTag", "Activity.Current", 
            "OpenTelemetry", "AddOpenTelemetry", "WithTracing",
            
            # Custom telemetry patterns  
            "Instrumentation", "TelemetryExtensions", "Monitoring",
            "Tracing", "Observability", "Metrics",
            
            # Configuration and setup
            "AddInstrumentation", "ConfigureServices", "UseOpenTelemetry",
            "TracerProvider", "MeterProvider",
            
            # Span and activity patterns
            "StartActivity", "StartSpan", "SetAttribute", "AddTag"
        ]
        
        for file_path, file_data in self.file_index.items():
            content = file_data["content"]
            imports = file_data.get("imports", [])
            patterns = file_data.get("patterns", [])
            
            matching_patterns = []
            relevance_score = 0
            
            # Check for telemetry imports
            for imp in imports:
                if any(pattern.lower() in imp.lower() for pattern in telemetry_patterns):
                    matching_patterns.append(f"Import: {imp}")
                    relevance_score += 15
            
            # Check for telemetry patterns in content
            for pattern in telemetry_patterns:
                if pattern in content:
                    matching_patterns.append(f"Pattern: {pattern}")
                    relevance_score += 10
            
            # Boost files that seem to be telemetry configuration
            file_name = Path(file_path).name.lower()
            if any(config_term in file_name for config_term in 
                   ["startup", "program", "telemetry", "instrumentation", "tracing"]):
                relevance_score += 20
                ##We have to change something here, too many config files! 
                matching_patterns.append(f"Config file: {file_name}")
            
            if matching_patterns:
                # Cap relevance score
                relevance_score = min(RelevanceScore.HIGH.value, relevance_score)
                
                context_snippets = []
                for pattern in telemetry_patterns[:3]: 
                    if pattern in content:
                        context_snippets.extend(self._extract_context_snippets(content, pattern))
                
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.PATTERN,
                    relevance_score=relevance_score,
                    reasoning=f"Telemetry infrastructure: {', '.join(matching_patterns[:3])}",
                    matching_patterns=matching_patterns,
                    context_snippets=context_snippets[:3],
                    confidence=0.85
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _structural_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on code structure patterns."""
        static_query = intent.get("static_analysis_query", {})
        if not static_query:
            return []
        
        results = []
        search_method = static_query.get("find_method_call")
        
        if search_method:
            for file_path, file_data in self.file_index.items():
                content = file_data["content"]
                
                # Search for method calls
                if search_method in content:
                    # Count occurrences for relevance scoring
                    occurrences = content.count(search_method)
                    relevance_score = min(RelevanceScore.EXACT_MATCH.value, 80 + occurrences * 5)
                    
                    # Extract context around matches
                    context_snippets = self._extract_method_context(content, search_method)
                    
                    result = SearchResult(
                        file_path=Path(file_path),
                        strategy=SearchStrategy.STRUCTURAL,
                        relevance_score=relevance_score,
                        reasoning=f"Contains method call: {search_method} ({occurrences} times)",
                        matching_patterns=[search_method],
                        context_snippets=context_snippets,
                        confidence=0.9 if occurrences > 1 else 0.7
                    )
                    results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _pattern_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on domain-specific patterns."""
        results = []
        
        # Search for telemetry patterns based on intent
        telemetry_op = intent.get("telemetry_operation", {})
        search_patterns = []
        
        # Add patterns based on operation type
        op_type = telemetry_op.get("type", "")
        if op_type in self.domain_knowledge.telemetry_patterns:
            search_patterns.extend(self.domain_knowledge.telemetry_patterns[op_type])
        
        # Add patterns based on attributes
        attributes = telemetry_op.get("attributes_to_add", [])
        for attr in attributes:
            attr_name = attr.get("name", "")
            if "." in attr_name:
                pattern_prefix = attr_name.split(".")[0]
                search_patterns.append(pattern_prefix)
        
        # Search for patterns in files
        for file_path, file_data in self.file_index.items():
            patterns_found = file_data.get("patterns", [])
            matching_patterns = []
            
            for pattern in search_patterns:
                if any(pattern.lower() in p.lower() for p in patterns_found):
                    matching_patterns.append(pattern)
            
            if matching_patterns:
                relevance_score = min(RelevanceScore.HIGH.value, 60 + len(matching_patterns) * 10)
                
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.PATTERN,
                    relevance_score=relevance_score,
                    reasoning=f"Matches patterns: {', '.join(matching_patterns)}",
                    matching_patterns=matching_patterns,
                    context_snippets=[],
                    confidence=0.8
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _keyword_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search based on keywords."""
        keywords = intent.get("search_keywords", [])
        if not keywords:
            return []
        
        results = []
        
        for file_path, file_data in self.file_index.items():
            content = file_data["content"]
            file_keywords = file_data.get("keywords", [])
            
            matches = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in content.lower() or keyword in file_keywords:
                    matches += 1
                    matched_keywords.append(keyword)
            
            if matches > 0:
                relevance_score = min(70, 40 + matches * 15)  # RelevanceScore.MEDIUM equivalent
                
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.KEYWORD,
                    relevance_score=relevance_score,
                    reasoning=f"Matches {matches} keywords: {', '.join(matched_keywords)}",
                    matching_patterns=matched_keywords,
                    context_snippets=[],
                    confidence=0.6
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _graph_based_search(self, intent: Dict, top_k: int) -> List[SearchResult]:
        """Search using code graph relationships."""
        print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Starting graph-based search with top_k={top_k}")
        if not self.code_graph_data:
            print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: No code graph data available")
            return []
        
        print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Code graph data available, processing {len(self.code_graph_data.symbols_by_file)} files")
        results = []
        
        # Extract telemetry-related terms from intent
        telemetry_terms = self._extract_telemetry_terms(intent)
        print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Extracted telemetry terms: {telemetry_terms}")
        
        # Use cached symbols_by_file for efficient iteration
        for file_path, symbols in self.code_graph_data.symbols_by_file.items():
            print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Processing file: {file_path}")
            # Skip if no file path
            if not file_path:
                print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Skipping file with empty path")
                continue
                
            # Convert to Path object
             # Resolve repo-relative paths from the code graph
            path_obj = Path(file_path)
            if not path_obj.is_absolute():
               path_obj = (self.repo_path / file_path).resolve()
            if not path_obj.exists():
               print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: File does not exist (after resolve): {path_obj}")
               continue
            
            # Calculate relevance based on multiple factors for this file
            relevance_score = 0
            matching_patterns = []
            reasoning_parts = []
            
            # 1. Check if file contains telemetry-related patterns
            if any(term.lower() in file_path.lower() for term in ["telemetry", "tracing", "span", "otel", "diagnostic"]):
                relevance_score += 30
                matching_patterns.append("telemetry_file_pattern")
                reasoning_parts.append("file path indicates telemetry functionality")
                print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Found telemetry pattern in file path: {file_path}")
            
            # 2. Check for HTTP/Web application patterns (key for ScmHttpApplication.cs)
            if any(term.lower() in file_path.lower() for term in ["http", "web", "application", "middleware", "startup"]):
                relevance_score += 25
                matching_patterns.append("web_application_pattern")
                reasoning_parts.append("file is part of web application infrastructure")
                
            # 3. Check for semantic conventions and configuration files
            if any(term.lower() in file_path.lower() for term in ["semantic", "convention", "config", "constants"]):
                relevance_score += 20
                matching_patterns.append("configuration_pattern")
                reasoning_parts.append("file contains configuration or constants")
            
            # 3a. Enhanced semantic conventions detection for HTTP telemetry
            if self._is_semantic_conventions_file(file_path, symbols):
                relevance_score += 35
                matching_patterns.append("semantic_conventions_pattern")
                reasoning_parts.append("file contains semantic conventions for telemetry attributes")
                print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Found semantic conventions file: {file_path}")
            
            # 4. Analyze symbols in this file for telemetry connections
            file_symbol_score = 0
            file_symbol_patterns = []
            file_symbol_reasoning = []
            
            for symbol in symbols:
                symbol_name = symbol.get("FullName", "")
                
                # Enhanced telemetry symbol matching
                if any(term in symbol_name.lower() for term in telemetry_terms):
                    file_symbol_score += 10
                    file_symbol_patterns.append(f"telemetry_symbol_{symbol_name}")
                    file_symbol_reasoning.append(f"contains telemetry symbol: {symbol_name}")
                
                # Look for HTTP-related constants that should be updated
                if any(term in symbol_name.upper() for term in ["HTTP", "REFERER", "REDIRECT", "LOCATION", "HEADER"]):
                    file_symbol_score += 15
                    file_symbol_patterns.append(f"http_constant_{symbol_name}")
                    file_symbol_reasoning.append(f"contains HTTP-related constant: {symbol_name}")
                    print(f"[DEBUG] IntelligentSearchEngine._graph_based_search: Found HTTP constant: {symbol_name} in {file_path}")
                
                # Check symbol relationships for telemetry connections
                relationships = symbol.get("Relationships", [])
                for rel in relationships:
                    target_name = rel.get("TargetSymbolFullName", "")
                    if any(term.lower() in target_name.lower() for term in telemetry_terms):
                        file_symbol_score += 15
                        file_symbol_patterns.append("telemetry_relationship")
                        file_symbol_reasoning.append(f"has relationship to telemetry symbol: {target_name}")
                        break
                
                # 5. Boost score for middleware and application entry points
                if any(term.lower() in symbol_name.lower() for term in ["middleware", "application", "startup", "configure"]):
                    file_symbol_score += 20
                    file_symbol_patterns.append("application_entry_point")
                    file_symbol_reasoning.append("symbol is application entry point or middleware")
            
            relevance_score += file_symbol_score
            matching_patterns.extend(file_symbol_patterns)
            reasoning_parts.extend(file_symbol_reasoning)
            
            # Only include if we have some relevance
            if relevance_score > 15 and matching_patterns:
                results.append(SearchResult(
                    file_path=path_obj,
                    relevance_score=min(relevance_score, 90),  # Cap at 90 for graph results
                    strategy=SearchStrategy.GRAPH_BASED,
                    matching_patterns=matching_patterns,
                    reasoning="; ".join(reasoning_parts),
                    confidence=0.8,  # High confidence for graph-based results
                    context_snippets=[]  # Graph-based search doesn't provide snippets
                ))
        
        # Sort by relevance and return top_k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    def _extract_telemetry_terms(self, intent: Dict) -> List[str]:
        """Extract telemetry-related terms from intent."""
        print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Extracting terms from intent: {intent}")
        terms = ["telemetry", "tracing", "span", "otel", "opentelemetry", "diagnostic"]
        
        # Add terms from intent
        if "static_analysis_query" in intent:
            static_query = intent["static_analysis_query"]
            print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Processing static_analysis_query: {static_query}")
            
            # Handle both string and dictionary formats
            if isinstance(static_query, dict):
                # Extract text from dictionary values
                query_text = " ".join(str(v).lower() for v in static_query.values())
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Converted dict to text: {query_text}")
            else:
                # Handle string format
                query_text = str(static_query).lower()
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Using string format: {query_text}")
            
            if "span" in query_text:
                terms.extend(["span", "activity", "StartActivity"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added span-related terms")
            if "attribute" in query_text or "tag" in query_text or "settag" in query_text:
                terms.extend(["attribute", "tag", "SetAttribute", "SetTag"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added attribute-related terms")
            if "trace" in query_text:
                terms.extend(["trace", "tracing"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added trace-related terms")
            if "http" in query_text:
                terms.extend(["http", "web", "request", "response", "redirect"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added HTTP-related terms")
            if "referer" in query_text or "referrer" in query_text:
                terms.extend(["referer", "referrer", "HTTP_REFERER"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added referer-related terms")
            if "redirect" in query_text:
                terms.extend(["redirect", "location", "HTTP_RESPONSE_REDIRECT_LOCATION"])
                print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Added redirect-related terms")
        
        print(f"[DEBUG] IntelligentSearchEngine._extract_telemetry_terms: Final terms: {terms}")
        return terms
    
    def _is_semantic_conventions_file(self, file_path: str, symbols: List[Dict]) -> bool:
        """Detect if this file contains semantic conventions or constants for telemetry."""
        print(f"[DEBUG] IntelligentSearchEngine._is_semantic_conventions_file: Checking {file_path}")
        
        # Check file name patterns
        file_name = file_path.lower()
        is_conventions_file = any(term in file_name for term in [
            "semantic", "conventions", "constants", "otel", "telemetry"
        ])
        
        # Look for constant patterns in symbols
        has_constants = any(
            s.get("Kind") == 6  # Field kind
            for s in symbols
        )
        
        # Look for HTTP or telemetry-related constants
        symbol_names = [s.get("FullName", "") for s in symbols]
        has_relevant_constants = any(
            any(term in name.upper() for term in ["HTTP", "HEADER", "TELEMETRY", "OTEL", "SEMANTIC"])
            for name in symbol_names
        )
        
        result = is_conventions_file and has_constants and has_relevant_constants
        print(f"[DEBUG] IntelligentSearchEngine._is_semantic_conventions_file: conventions_file={is_conventions_file}, has_constants={has_constants}, relevant_constants={has_relevant_constants}, result={result}")
        
        return result
    
    def _consolidate_results(self, all_results: List[SearchResult]) -> List[SearchResult]:
        """
        Consolidate results from different strategies, handling duplicates.
        
        UNIVERSAL IMPROVEMENT: Add reality validation during consolidation.
        """
        file_to_results = {}
        
        for result in all_results:
            file_path = str(result.file_path)
            
            # UNIVERSAL IMPROVEMENT: Reality check - does the file actually exist?
            if not result.file_path.exists():
                print(f"Warning: Search result points to non-existent file: {file_path}")
                continue
            
            # UNIVERSAL IMPROVEMENT: Additional quality checks
            if not self._is_valid_search_result(result):
                continue
            
            if file_path not in file_to_results:
                file_to_results[file_path] = result
            else:
                # Merge results for the same file
                existing = file_to_results[file_path]
                
                # Take the higher relevance score
                if result.relevance_score > existing.relevance_score:
                    file_to_results[file_path] = result
                
                # Merge matching patterns
                existing.matching_patterns.extend(result.matching_patterns)
                existing.matching_patterns = list(set(existing.matching_patterns))
                
                # Combine reasoning
                existing.reasoning += f"; {result.reasoning}"
                
                # Take higher confidence
                existing.confidence = max(existing.confidence, result.confidence)
        
        return list(file_to_results.values())
    
    def _is_valid_search_result(self, result: SearchResult) -> bool:
        """
        UNIVERSAL IMPROVEMENT: Validate that search results are actually useful.
        
        WHY: Prevents irrelevant files from cluttering results, even if they 
        somehow passed the initial filters.
        
        BEFORE: Would include any file that had keyword matches
        AFTER: Validates that the file is actually relevant for telemetry work
        """
        file_path = result.file_path
        
        # Check file size - empty files or extremely large files are usually not useful
        try:
            file_size = file_path.stat().st_size
            if file_size == 0 or file_size > 10 * 1024 * 1024:  # Skip files > 10MB
                return False
        except:
            return False
        
        # Check if file extension is appropriate
        if not file_path.suffix.lower() in ['.cs', '.fs', '.vb']:
            return False
        
        # Check relevance score threshold
        if result.relevance_score < 20:  # Minimum relevance threshold
            return False
        
        # Ensure we have actual patterns or reasoning
        if not result.matching_patterns and not result.reasoning:
            return False
        
        return True
    
    

    
    def _apply_domain_ranking(self, results: List[SearchResult], intent: Dict) -> List[SearchResult]:
        """Apply domain-specific ranking adjustments."""
        for result in results:
            file_path = str(result.file_path)
            file_data = self.file_index.get(file_path, {})
            
            # Boost configuration files for configuration intents
            if intent.get("issue_category") == "CONFIGURATION":
                if any(pattern in file_path.lower() for pattern in 
                    ["startup", "program", "extensions", "configuration"]):
                    result.relevance_score += 15
            
            # Boost files with telemetry imports
            imports = file_data.get("imports", [])
            if any("opentelemetry" in imp.lower() for imp in imports):
                result.relevance_score += 10
            
            # Boost files that already have instrumentation
            patterns = file_data.get("patterns", [])
            if any("telemetry" in pattern for pattern in patterns):
                result.relevance_score += 10
            
            # Penalize test files unless specifically looking for test patterns
            if "test" in file_path.lower() and "test" not in intent.get("semantic_description", "").lower():
                result.relevance_score -= 20
            
            # Ensure relevance score stays within bounds
            result.relevance_score = max(0, min(100, result.relevance_score))
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)


    
    def _extract_context_snippets(self, content: str, query: str) -> List[str]:
        """Extract relevant context snippets from file content."""
        lines = content.split('\n')
        snippets = []
        query_terms = query.lower().split()
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(term in line_lower for term in query_terms):
                # Extract context around the matching line
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                snippets.append(context.strip())
        
        return snippets[:3]  # Return top 3 snippets
    
    def _find_telemetry_configuration_files(self, top_k: int) -> List[SearchResult]:
        """Find files that configure telemetry - these are prime targets for configuration changes."""
        results = []
        
        for file_path, file_info in self.file_index.items():
            content = file_info["content"]
            
            # Look for telemetry configuration patterns
            telemetry_score = 0
            matching_patterns = []
            
            # Check for service collection extensions (primary target)
            if "IServiceCollection" in content and any(pattern in content for pattern in ["AddOpenTelemetry", "AddSqlClientInstrumentation", "AddHttpClientInstrumentation"]):
                telemetry_score += 50
                matching_patterns.append("ServiceCollection telemetry setup")
            
            # Check for startup/program files
            if any(pattern in file_path.lower() for pattern in ["startup", "program", "serviceextensions"]):
                telemetry_score += 30
                matching_patterns.append("Application startup")
            
            # Check for specific instrumentation calls
            for instr_pattern in ["AddSqlClientInstrumentation", "AddHttpClientInstrumentation", "AddAspNetCoreInstrumentation"]:
                if instr_pattern in content:
                    telemetry_score += 25
                    matching_patterns.append(f"{instr_pattern} configuration")
            
            if telemetry_score > 0:
                result = SearchResult(
                    file_path=Path(file_path),
                    strategy=SearchStrategy.STRUCTURAL,
                    relevance_score=min(telemetry_score, 95),
                    reasoning=f"Telemetry configuration file: {', '.join(matching_patterns)}",
                    matching_patterns=matching_patterns,
                    context_snippets=self._extract_context_snippets(content, "AddOpenTelemetry"),
                    confidence=0.9
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)[:top_k]
    
    def _extract_method_context(self, content: str, method_name: str) -> List[str]:
        """Extract context around method calls."""
        lines = content.split('\n')
        contexts = []
        
        for i, line in enumerate(lines):
            if method_name in line:
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = '\n'.join(lines[start:end])
                contexts.append(context.strip())
        
        return contexts
