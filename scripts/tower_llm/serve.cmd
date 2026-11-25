@echo off
rem Hive Drone: Ollama on localhost only, one model at a time, unloads 2 min after the last job.
set OLLAMA_HOST=127.0.0.1:11434
set OLLAMA_KEEP_ALIVE=2m
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_FLASH_ATTENTION=1
set OLLAMA_KV_CACHE_TYPE=q8_0
ollama serve
