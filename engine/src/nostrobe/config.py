"""Environment and application-path configuration at the edge."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOSTROBE_", frozen=True)
    repo_root: Path = Path(__file__).resolve().parents[3]
    ffmpeg: str = "ffmpeg"
    ffprobe: str = "ffprobe"
    log_level: str = "INFO"

    @property
    def cache_dir(self) -> Path:
        return self.repo_root / ".nostrobe_cache"

    @property
    def synth_dir(self) -> Path:
        return self.repo_root / "synth_out"

    @property
    def schema_path(self) -> Path:
        return self.repo_root / "spec/schema/hazardtrack.schema.json"

    @property
    def eval_manifest(self) -> Path:
        return self.repo_root / "engine/eval/manifest.yaml"

    @property
    def eval_sources(self) -> Path:
        return self.repo_root / "synth_out/s4/sources"

    @property
    def eval_output(self) -> Path:
        return self.repo_root / "engine/eval"
