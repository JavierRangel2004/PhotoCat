"""
device.py — Centralized hardware detection for PhotoCat.

Detects the best compute device across platforms:
- Windows/Linux with NVIDIA GPU (CUDA)
- macOS with Apple Silicon (MPS)
- macOS with Intel / CPU fallback
"""

import platform
import torch


def detect_device():
    """Detect the best available compute device. Returns (device_str, info_dict)."""
    info = {
        "platform": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        "device": "cpu",
        "gpu_name": None,
        "vram_total_mb": None,
        "vram_free_mb": None,
    }

    if info["cuda_available"]:
        info["device"] = "cuda"
        info["gpu_name"] = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        total = getattr(props, "total_memory", None) or getattr(props, "total_mem", 0)
        info["vram_total_mb"] = round(total / 1024**2)
        info["vram_free_mb"] = round((total - torch.cuda.memory_allocated(0)) / 1024**2)
    elif info["mps_available"]:
        info["device"] = "mps"
        info["gpu_name"] = "Apple Silicon (MPS)"

    return info["device"], info


def print_device_info(info):
    """Print a compact summary of detected hardware."""
    print(f"[Device] {info['platform']} {info['arch']} | PyTorch {info['torch']}")
    if info["device"] == "cuda":
        print(f"[Device] GPU: {info['gpu_name']} | VRAM: {info['vram_total_mb']} MB total, ~{info['vram_free_mb']} MB free")
        print(f"[Device] Compute: CUDA")
    elif info["device"] == "mps":
        print(f"[Device] GPU: {info['gpu_name']}")
        print(f"[Device] Compute: MPS (Apple Silicon)")
    else:
        print(f"[Device] GPU: None detected | Compute: CPU")
        if info["platform"] in ("Windows", "Linux") and not info["cuda_available"]:
            print(f"[Device] TIP: Install CUDA-enabled PyTorch for GPU acceleration:")
            print(f"[Device]   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")


# Module-level singleton — computed once, reused everywhere
_device = None
_device_info = None


def get_device():
    """Return the best device string ('cuda', 'mps', or 'cpu'). Cached."""
    global _device, _device_info
    if _device is None:
        _device, _device_info = detect_device()
    return _device


def get_device_info():
    """Return the full device info dict. Cached."""
    global _device, _device_info
    if _device is None:
        _device, _device_info = detect_device()
    return _device_info
