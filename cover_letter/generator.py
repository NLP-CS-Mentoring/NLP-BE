# 자소서 생성
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_cover_letter(user_fact, style_guide=None):
    """ 사용자의 스타일을 반영하여 자소서를 생성 """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    if not style_guide:
        style_guide = "신뢰감을 주는 정중한 비즈니스 문체 (기본값)"

    prompt = PromptTemplate.from_template(
        """
        당신은 전문 에디터입니다. 
        아래 [스타일 가이드]의 어조와 문체를 100% 반영하여, [사용자 경험]을 자기소개서를 작성하세요.
        
        [스타일 가이드]:
        {style}
        
        [사용자 경험(Facts)]:
        {fact}
        
        ---
        작성 지침:
        - 팩트를 과장하지 말고 주어진 내용 안에서 서술하세요.
        - 문단은 서론-본론-결론 구조를 갖추세요.
        - 글자 수는 공백 제외 약 500자 내외.
        
        [생성된 자기소개서]:
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {
            "style": style_guide, 
            "fact": user_fact,
        }
    )
