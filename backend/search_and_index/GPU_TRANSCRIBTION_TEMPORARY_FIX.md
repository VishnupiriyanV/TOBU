If you want to use GPU for transcribing in faster-whisper ,

then change "cpu" to "cuda" in the aural_engine.py 

after running it you might run into this runtime error:

"RuntimeError: Library cublas64_12.dll is not found or cannot be loaded"

to fix this install these to libs: (make sure it is in venv)

pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

and if the issues still persists, then copy the dll files from these paths

.venv\Lib\site-packages\nvidia\cublas\bin
.venv\Lib\site-packages\nvidia\cudnn\bin

and paste it in 

.venv\Lib\site-packages\ctranslate2

it should solve the issue for now 
but need to find something different for the final version though