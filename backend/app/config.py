import os

from pydantic import BaseModel, Field, HttpUrl


class Settings(BaseModel):
    crawlab_base_url: HttpUrl = HttpUrl("http://master:8080/api/")
    public_origin: str = "http://localhost:8080"
    session_secret: str = Field(min_length=32)
    cookie_secure: bool = False

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            crawlab_base_url=os.environ.get("CRAWLAB_BASE_URL", "http://master:8080/api/"),
            public_origin=os.environ.get("FLOWHARBOR_PUBLIC_ORIGIN", "http://localhost:8080").rstrip("/"),
            session_secret=os.environ["FLOWHARBOR_SESSION_SECRET"],
            cookie_secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        )
