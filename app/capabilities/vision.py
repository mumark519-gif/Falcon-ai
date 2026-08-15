from __future__ import annotations
import base64
from app.services.ai.ai_gateway import generate
class VisionCapability:
    def describe(self,image_path:str,prompt="Describe this image in detail.",**kwargs):
        from app.services.ai.providers import router
        p=router.get(kwargs.get("provider","openai"))
        if p.name!="openai": raise RuntimeError("Vision adapter currently requires an OpenAI-capable provider")
        from openai import OpenAI
        c=OpenAI(api_key=p.key)
        mime="image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        data=base64.b64encode(open(image_path,"rb").read()).decode()
        r=c.responses.create(model=kwargs.get("model",p.model),input=[{"role":"user","content":[{"type":"input_text","text":prompt},{"type":"input_image","image_url":f"data:{mime};base64,{data}"}]}])
        return getattr(r,"output_text","")
