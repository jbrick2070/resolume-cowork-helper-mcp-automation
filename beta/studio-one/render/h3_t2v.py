"""Local MiniMax H3 text-to-video, same settings as the Earthsearch/Buck Rogers production graph
(fl2va pruned int8 UNet, 20 steps, res_multistep/simple, no LoRA) minus the image and audio guides.

usage: python -I h3_t2v.py ID PROMPT_FILE WIDTH HEIGHT SEED TAG
Writes shots/<ID>_<TAG>.mp4 (picture only) and prints one JSON line.
"""
import json
import os
import shutil
import subprocess
import sys
import time

W = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SHOTS = W + "/shots"
COMFY_OUT = os.environ.get("COMFY_OUT", "C:/ComfyUI/output")   # your ComfyUI output folder
PY = sys.executable

cid, prompt_file, width, height, seed, tag = sys.argv[1:7]
width, height, seed = int(width), int(height), int(seed)
TURBO = "--turbo" in sys.argv          # the template's Lightning switch: 8-step LoRA, 6 steps
VAE = ("minimax_h3_video_vae_int8_convrot.safetensors" if "--int8vae" in sys.argv
       else "minimax_h3_video_vae_fp16.safetensors")
name = f"{cid}_{tag}"
prompt = open(prompt_file, encoding="utf-8").read().strip()
# H3's audio branch is not used here; drop the trailing Audio sentence so the prompt is picture only
if "Audio:" in prompt:
    prompt = prompt[:prompt.index("Audio:")].strip()

g = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
                                                 "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                                                 "type": "minimax", "device": "default"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
    "8": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt,
                                                            "width": width, "height": height, "length": 124}},
    "10": {"class_type": "BasicScheduler", "inputs": {"model": ["1", 0], "scheduler": "simple", "steps": 20,
                                                      "denoise": 1.0}},
    "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
    "12": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
    "13": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["8", 0]}},
    "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["12", 0], "guider": ["13", 0],
                                                             "sampler": ["11", 0], "sigmas": ["10", 0],
                                                             "latent_image": ["8", 1]}},
    "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["3", 0]}},
    "17": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 24.0}},
    "18": {"class_type": "SaveVideo", "inputs": {"video": ["17", 0], "filename_prefix": f"studio_one/{name}",
                                                 "format": "auto", "codec": "auto"}},
}
if TURBO:
    g["5"] = {"class_type": "LoraLoaderModelOnly",
              "inputs": {"model": ["1", 0], "strength_model": 1.0,
                         "lora_name": "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"}}
    g["10"]["inputs"].update({"model": ["5", 0], "steps": 6})
    g["13"]["inputs"]["model"] = ["5", 0]
api = f"{W}/api/{name}.json"
os.makedirs(f"{W}/api", exist_ok=True)
with open(api, "w", encoding="utf-8") as fh:
    json.dump(g, fh, indent=1)
if "--build-only" in sys.argv:
    print(json.dumps({"id": cid, "api": api}))
    sys.exit(0)

t0 = time.time()
r = subprocess.run([PY, "-I", f"{W}/run_api.py", api, "5400"], capture_output=True, text=True)
lines = [ln for ln in r.stdout.strip().splitlines() if ln.startswith("{")]
res = json.loads(lines[-1]) if lines else {"ok": False, "error": (r.stdout + r.stderr)[-1200:]}
out = {"id": cid, "tag": tag, "ok": bool(res.get("ok")), "render_seconds": round(time.time() - t0, 1)}
if res.get("ok"):
    src = f"{COMFY_OUT}/{res['files'][0]}"
    mp4 = f"{SHOTS}/{name}.mp4"
    shutil.copyfile(src, mp4)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=1.6,scale=480:-2,tile=4x2",
                    "-frames:v", "1", "-q:v", "3", f"{SHOTS}/{name}_sheet.jpg"], check=False)
    out["mp4"] = mp4
else:
    out["error"] = json.dumps(res)[-1200:]
print(json.dumps(out), flush=True)
