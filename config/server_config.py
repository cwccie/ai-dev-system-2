{
  "servers": {
    "server1": {
      "name": "Main Development Server",
      "url": "http://server1:11434",
      "max_concurrent_tasks": 3,
      "models": [
        "codellama:34b",
        "wizardcoder:15b",
        "starcoder:15.5b"
      ],
      "model_roles": {
        "codellama:34b": ["coding"],
        "wizardcoder:15b": ["coding"],
        "starcoder:15.5b": ["coding"]
      },
      "gpu": "A100 40GB",
      "priority": 1
    },
    "server2": {
      "name": "Orchestration Server",
      "url": "http://server2:11434",
      "max_concurrent_tasks": 3,
      "models": [
        "llama2:70b",
        "llama2:13b",
        "mpt:30b"
      ],
      "model_roles": {
        "llama2:70b": ["orchestration"],
        "llama2:13b": ["orchestration"],
        "mpt:30b": ["orchestration"]
      },
      "gpu": "A100 80GB",
      "priority": 1
    },
    "server3": {
      "name": "Mixed Workload Server",
      "url": "http://server3:11434",
      "max_concurrent_tasks": 3,
      "models": [
        "codellama:13b",
        "wizardlm:30b",
        "vicuna:13b"
      ],
      "model_roles": {
        "codellama:13b": ["coding"],
        "wizardlm:30b": ["orchestration"],
        "vicuna:13b": ["orchestration"]
      },
      "gpu": "RTX 4090",
      "priority": 2
    },
    "server4": {
      "name": "Lightweight Models Server",
      "url": "http://server4:11434",
      "max_concurrent_tasks": 3,
      "models": [
        "codellama:7b",
        "llama2:7b",
        "wizardcoder:7b"
      ],
      "model_roles": {
        "codellama:7b": ["coding"],
        "llama2:7b": ["orchestration"],
        "wizardcoder:7b": ["coding"]
      },
      "gpu": "RTX 3090",
      "priority": 3
    }
  },
  "model_rankings": {
    "coding": [
      {
        "model": "codellama:34b",
        "rank": 1,
        "server_id": "server1",
        "parameter_count": "34B",
        "strengths": ["Excellent multi-language code performance", "strong Python generation", "robust context handling"]
      },
      {
        "model": "llama2:70b",
        "rank": 2,
        "server_id": "server2",
        "parameter_count": "70B",
        "strengths": ["High-quality coding responses", "superior reasoning in complex tasks", "excels with large context windows"]
      },
      {
        "model": "starcoder:15.5b",
        "rank": 3,
        "server_id": "server1",
        "parameter_count": "15.5B",
        "strengths": ["Specifically trained on code", "outstanding Python and shell scripts", "extensive open-source benchmarks"]
      },
      {
        "model": "wizardcoder:15b",
        "rank": 4,
        "server_id": "server1",
        "parameter_count": "15B",
        "strengths": ["Optimized for coding tasks", "fine-tuned to answer complex queries in Python, Java, and more"]
      },
      {
        "model": "mpt:30b",
        "rank": 5,
        "server_id": "server2",
        "parameter_count": "30B",
        "strengths": ["Strong multi-round reasoning and coding proficiency", "good open-source community support"]
      },
      {
        "model": "codellama:13b",
        "rank": 6,
        "server_id": "server3",
        "parameter_count": "13B",
        "strengths": ["Balanced performance for code generation", "especially Python-centric workflows"]
      },
      {
        "model": "wizardcoder:7b",
        "rank": 7,
        "server_id": "server4",
        "parameter_count": "7B",
        "strengths": ["Smaller variant specialized in code suggestions and direct completions"]
      },
      {
        "model": "codellama:7b",
        "rank": 8,
        "server_id": "server4",
        "parameter_count": "7B",
        "strengths": ["Reliable base for coding under tighter resource constraints", "good for straightforward code snippets"]
      }
    ],
    "orchestration": [
      {
        "model": "llama2:70b",
        "rank": 1,
        "server_id": "server2",
        "parameter_count": "70B",
        "strengths": ["Exceptional multi-step reasoning", "long-context support", "strong instruction-following for complex orchestration"]
      },
      {
        "model": "mpt:30b",
        "rank": 2,
        "server_id": "server2",
        "parameter_count": "30B",
        "strengths": ["Large context window and robust chain-of-thought approach", "well-suited for planning and delegating"]
      },
      {
        "model": "wizardlm:30b",
        "rank": 3,
        "server_id": "server3",
        "parameter_count": "30B",
        "strengths": ["Specializes in detailed step-by-step reasoning and iterative problem-solving", "aiding orchestrator scenarios"]
      },
      {
        "model": "llama2:13b",
        "rank": 4,
        "server_id": "server2",
        "parameter_count": "13B",
        "strengths": ["Lighter variant but inherits strong multi-turn reasoning from Llama 2 family", "effective for orchestrating smaller projects"]
      },
      {
        "model": "vicuna:13b",
        "rank": 5,
        "server_id": "server3",
        "parameter_count": "13B",
        "strengths": ["Known for conversational depth", "which translates well into multi-agent directive tasks and collaborative flows"]
      },
      {
        "model": "llama2:7b",
        "rank": 6,
        "server_id": "server4",
        "parameter_count": "7B",
        "strengths": ["Similar strengths to the 13B version but with tighter resource use", "good for smaller orchestrator frameworks"]
      }
    ]
  },
  "settings": {
    "timeout_seconds": 300,
    "auto_failover": true,
    "prefer_higher_rank": true,
    "task_specific_selection": true,
    "status_check_interval_minutes": 5,
    "max_retry_attempts": 3
  }
}
