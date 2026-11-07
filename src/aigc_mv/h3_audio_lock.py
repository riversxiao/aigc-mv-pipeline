"""ComfyUI node: generate video while preserving an externally supplied song clock."""
import torch
from comfy.nested_tensor import NestedTensor


class H3LockGuideAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"latent": ("LATENT",), "audio_vae": ("VAE",), "audio": ("AUDIO",)}}

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "lock_audio"
    CATEGORY = "MiniMax-H3/Audio"

    def lock_audio(self, latent, audio_vae, audio):
        samples = latent["samples"]
        if not samples.is_nested or len(samples.tensors) != 2:
            raise ValueError("Expected joint H3 video/audio latent")
        video, target = samples.tensors
        if audio["sample_rate"] != getattr(audio_vae, "audio_sample_rate", 32000):
            raise ValueError("Guide audio must already match the audio VAE sample rate")
        encoded = audio_vae.encode(audio["waveform"][:1].movedim(1, -1))
        if encoded.shape[:-1] != target.shape[:-1]:
            raise ValueError("Guide audio latent channel layout does not match H3")
        # Keep the audio clock. Only the trailing padded silence may be trimmed/padded.
        encoded = encoded[..., :target.shape[-1]].clone()
        if encoded.shape[-1] < target.shape[-1]:
            encoded = torch.nn.functional.pad(encoded, (0, target.shape[-1] - encoded.shape[-1]))
        encoded = encoded.to(device=target.device, dtype=target.dtype)
        out = latent.copy()
        out["samples"] = NestedTensor((video, encoded))
        # 1 = generate, 0 = preserve. The original song is never denoised/recomposed.
        out["noise_mask"] = NestedTensor((torch.ones_like(video), torch.zeros_like(encoded)))
        return (out,)


NODE_CLASS_MAPPINGS = {"H3LockGuideAudio": H3LockGuideAudio}
NODE_DISPLAY_NAME_MAPPINGS = {"H3LockGuideAudio": "H3 Lock Guide Audio (Video Only Sampling)"}
