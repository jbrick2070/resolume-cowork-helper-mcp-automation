# render/

The scripts that made twenty of the forty FILM clips, locally, on MiniMax H3.

* `make_prompts.py` writes `prompts/<scene>.txt` for all 40 scenes.
* `h3_t2v.py ID PROMPT_FILE WIDTH HEIGHT SEED TAG [--turbo] [--int8vae]` builds the ComfyUI graph
  (UNETLoader `minimax_h3_fl2va_pruned_int8_convrot`, CLIPLoader qwen3vl_32b nvfp4, text-to-video,
  20 steps res_multistep/simple, or `--turbo` = the official 8-step LoRA at 6 steps), queues it
  through `run_api.py` on 127.0.0.1:8000 and copies the result to `shots/`.
* Used at 1920x1088 with `--turbo --int8vae`; crop to 1920x1080 afterwards
  (`ffmpeg -vf crop=1920:1080:0:4`). Height must be a multiple of 32. Set `COMFY_OUT` to your
  ComfyUI output folder. On a 16 GB card the weights stream from RAM and a clip takes about 16 minutes.
* The H3 files come from `Comfy-Org/MiniMax-H3` on Hugging Face.
