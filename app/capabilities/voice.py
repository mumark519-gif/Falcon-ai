from __future__ import annotations
from pathlib import Path
from typing import Any
class VoiceCapability:
    def transcribe(self,path:str,**kwargs)->dict[str,Any]:
        from app.services.ai.providers import router
        provider=router.get("openai")
        from openai import OpenAI
        c=OpenAI(api_key=provider.key)
        with open(path,"rb") as f: r=c.audio.transcriptions.create(model=kwargs.get("model","gpt-4o-mini-transcribe"),file=f)
        return {"text":getattr(r,"text","")}
    def synthesize(self,text:str,output_path:str,**kwargs)->str:
        from app.services.ai.providers import router
        p=router.get("openai")
        from openai import OpenAI
        c=OpenAI(api_key=p.key)
        with c.audio.speech.with_streaming_response.create(model=kwargs.get("model","gpt-4o-mini-tts"),voice=kwargs.get("voice","alloy"),input=text) as r:
            r.stream_to_file(output_path)
        return output_path
