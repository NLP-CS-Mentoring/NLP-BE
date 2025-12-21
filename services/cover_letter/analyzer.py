# 스타일 분석
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def analyze_style(reference_text):
    """ 사용자의 글을 분석하여 어투를 추출 """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    prompt = PromptTemplate.from_template(
        """
        당신은 텍스트 스타일리스트입니다. 
        제공된 [참조 텍스트]를 분석하여 글쓴이의 고유한 '글쓰기 스타일'을 요약해 주세요.
        
        분석 포인트:
        1. 문체의 분위기 (예: 건조함, 열정적, 논리적)
        2. 종결어미의 특징 (예: ~했습니다, ~함, ~다, ~임)
        3. 문장의 호흡 (단문 위주 vs 만연체)
        4. 자주 쓰는 어휘의 수준

        [참조 텍스트]:
        {text}

        [스타일 분석 결과 (3줄 요약)]:
        """
    )

    chain = prompt | llm | StrOutputParser()
    
    # 앞에서부터 3000자만 자름
    return chain.invoke({"text": reference_text[:3000]})
