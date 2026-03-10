from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, Session, SQLModel, StaticPool, create_engine

from medium.passwords import hash_password


class ArticleStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNLISTED = "unlisted"


class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    author_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    title: str
    slug: str | None
    subtitle: str | None
    json_content: str
    text_content: str
    markdown_content: str
    html_content: str
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT, index=True)

    author: Optional["User"] = Relationship(back_populates="articles")


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    password_hash: str

    articles: list["Article"] = Relationship(back_populates="author")
    sessions: list["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    session_hash: str = Field(primary_key=True)
    user_id: int = Field(default=None, primary_key=True, foreign_key="user.id")
    expires_at: datetime = Field(index=True)
    revoked_at: datetime | None = Field(default=None, index=True)

    user: Optional["User"] = Relationship(back_populates="sessions")


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True,
)
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    user = User(
        email="user@email.com",
        username="testuser",
        password_hash=hash_password("password"),
    )
    article = Article(
        title="Medium (website)",
        slug="medium",
        subtitle="An online publishing platform",
        json_content="""{"type":"doc","content":[{"type":"heading","attrs":{"level":1},"content":[{"type":"text","text":"Medium (website)"}]},{"type":"paragraph","content":[{"type":"text","marks":[{"type":"bold"}],"text":"Medium"},{"type":"text","text":" is an American "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Electronic_publishing","target":"_blank","rel":"noopener noreferrer nofollow","class":null,"title":"Electronic publishing"}}],"text":"online publishing platform"},{"type":"text","text":" for written content such as articles and blogs, developed by "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Evan_Williams_(Internet_entrepreneur)","target":"_blank","rel":"noopener noreferrer nofollow","class":null,"title":"Evan Williams (Internet entrepreneur)"}}],"text":"Evan Williams"},{"type":"text","text":" and launched in August 2012. It is owned by "},{"type":"text","marks":[{"type":"bold"}],"text":"A Medium Corporation"},{"type":"text","text":". The platform is an example of "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Social_journalism","target":"_blank","rel":"noopener noreferrer nofollow","class":null,"title":"Social journalism"}}],"text":"social journalism"},{"type":"text","text":", having a hybrid collection of amateur and professional people and publications, or exclusive blogs or publishers on Medium, and is regularly regarded as a "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Blog","target":"_blank","rel":"noopener noreferrer nofollow","class":null,"title":"Blog"}}],"text":"blog host"},{"type":"text","text":"."}]},{"type":"paragraph","content":[{"type":"text","text":"Williams, who previously co-founded "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Blogger_(service)","target":"_blank","rel":"noopener noreferrer nofollow","class":null,"title":"Blogger (service)"}}],"text":"Blogger"},{"type":"text","text":" and "},{"type":"text","marks":[{"type":"link","attrs":{"href":"https://en.wikipedia.org/wiki/Twitter","target":"_blank","rel":"noopener noreferrer nofollow","class":"mw-redirect","title":"Twitter"}}],"text":"Twitter"},{"type":"text","text":", initially developed Medium as a means to publish writings and documents longer than Twitter's then 140-character maximum."}]},{"type":"paragraph","content":[{"type":"text","text":"In March 2021, Medium announced a change in its publishing strategy and business model, reducing its own publications and increasing support of independent writers."}]}]}""",
        text_content="""Medium (website)\nMedium is an American online publishing platform for written content such as articles and blogs, developed by Evan Williams and launched in August 2012. It is owned by A Medium Corporation. The platform is an example of social journalism, having a hybrid collection of amateur and professional people and publications, or exclusive blogs or publishers on Medium, and is regularly regarded as a blog host.\nWilliams, who previously co-founded Blogger and Twitter, initially developed Medium as a means to publish writings and documents longer than Twitter's then 140-character maximum.\nIn March 2021, Medium announced a change in its publishing strategy and business model, reducing its own publications and increasing support of independent writers.""",
        markdown_content="""# Medium (website)\n**Medium** is an American [online publishing platform](https://en.wikipedia.org/wiki/Electronic_publishing) for written content such as articles and blogs, developed by [Evan Williams](https://en.wikipedia.org/wiki/Evan_Williams_(Internet_entrepreneur)) and launched in August 2012. It is owned by **A Medium Corporation**. The platform is an example of [social journalism](https://en.wikipedia.org/wiki/Social_journalism), having a hybrid collection of amateur and professional people and publications, or exclusive blogs or publishers on Medium, and is regularly regarded as a [blog host](https://en.wikipedia.org/wiki/Blog).\nWilliams, who previously co-founded [Blogger](https://en.wikipedia.org/wiki/Blogger_(service)) and [Twitter](https://en.wikipedia.org/wiki/Twitter), initially developed Medium as a means to publish writings and documents longer than Twitter's then 140-character maximum.\nIn March 2021, Medium announced a change in its publishing strategy and business model, reducing its own publications and increasing support of independent writers.""",
        html_content="""<h1>Medium (website)</h1><p><b>Medium</b> is an American <a href="/wiki/Electronic_publishing" title="Electronic publishing">online publishing platform</a> for written content such as articles and blogs, developed by <a href="/wiki/Evan_Williams_(Internet_entrepreneur)" title="Evan Williams (Internet entrepreneur)">Evan Williams</a> and launched in August 2012. It is owned by <b>A Medium Corporation</b>. The platform is an example of <a href="/wiki/Social_journalism" title="Social journalism">social journalism</a>, having a hybrid collection of amateur and professional people and publications, or exclusive blogs or publishers on Medium, and is regularly regarded as a <a href="/wiki/Blog" title="Blog">blog host</a>.</p><p>Williams, who previously co-founded <a href="/wiki/Blogger_(service)" title="Blogger (service)">Blogger</a> and <a href="/wiki/Twitter" class="mw-redirect" title="Twitter">Twitter</a>, initially developed Medium as a means to publish writings and documents longer than Twitter's then 140-character maximum.</p><p>In March 2021, Medium announced a change in its publishing strategy and business model, reducing its own publications and increasing support of independent writers.</p>""",
        status=ArticleStatus.PUBLISHED,
        author=user,
    )
    session.add(user)
    session.add(article)
    session.commit()
