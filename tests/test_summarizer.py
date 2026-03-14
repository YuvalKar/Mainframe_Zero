import asyncio
import json
import sys
import os

# Add the parent directory to Python's path so it can find 'workers'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now we can import the agent from the workers package
from workers.summarizer_agent import SummarizerAgent

async def run_test():
    print("Starting the test environment...")
    
    # Initialize our summarizer agent
    agent = SummarizerAgent()
    
    # Paste your text here or load it from a file
    sample_text = """
    העתקתי הכל, אני מוכן לבדיקה. בנה לי קובץ של בדיקה, אני אטען את הטקסט עצמו

    Gemini אמר
    איזה כיף, הגענו לחלק האהוב עליי במסע – רגע האמת שבו מריצים את הקוד ומגלים אם עשינו קסם, או שעוד שנייה הכל קורס לנו מול העיניים עם איזה טרייסבאק (Traceback) ארוך של פייתון.

    כדי לבדוק את זה כמו שצריך בסביבה אסינכרונית, אנחנו צריכים סקריפט קטן שיעלה את הסוכן לאוויר ברקע, יזרוק לו משימה לתור, ויחכה שהוא יסיים.

    הכנתי לך את קובץ הטסט. שים לב שהשארתי לך שם מקום ברור להדביק את הטקסט שלך (או לטעון מקובץ, מה שנוח לך).

    הנה test_summarizer.py:

    Python
    import asyncio
    import json
    # Make sure the import matches your actual file name
    from summarizer_agent import SummarizerAgent

    async def run_test():
        print("Starting the test environment...")
        
        # 1. Initialize our summarizer agent
        agent = SummarizerAgent()
        
        # 2. Fire up the background worker task
        # We use create_task so it runs independently in the background
        worker_task = asyncio.create_task(agent.start())


    if __name__ == "__main__":
        # Run the main async loop
        asyncio.run(run_test())
    רגע לפני שאתה מריץ, עליתי פה על קאצ' קטן שיכול לשגע אותנו:
    אם תסתכל ב-worker_base.py שכתבת בהתחלה, שים לב שבלולאת ה-while, אתה קורא ל-await self.process_task(task), אבל אתה לא תופס את התשובה שחוזרת (ה-return) ולא מדפיס אותה. זה אומר שהסוכן יעבוד, יסכם הכל מושלם, ואנחנו לא נראה כלום על המסך! קלאסי, הא? קרה לי אלף פעם.

    אז רק לצורך הבדיקה שלנו, קפוץ רגע ל-SummarizerAgent שלך, וממש לפני ה-return result בסוף ה-try, תוסיף שורת הדפסה פשוטה:

    Python
                # Just to see it works during our test!
                print(json.dumps(result, indent=4, ensure_ascii=False))
                return result
    תריץ את זה, תראה איזה פלט אתה מקבל, ותגיד לי אם ג'מיני הקשיב לנו והחזיר JSON נקי או שהוא שוב עשה שטויות ונצטרך לתקן. איך יצא?

    אמרת
    למה שהtest לא יהיה זה שידפיס? לא רוצה לגעת בפונקציה עצמה
    Gemini אמר
    אתה צודק ב-100%, ותפסת אותי פה מעגל פינות. זה אנטי-תבנית (Anti-pattern) קלאסי לגעת בקוד מבצעי וללכלך אותו בהדפסות רק בשביל שטסט יעבוד. מודה, יצאתי פה קצת "גורו" שמנסה לדחוף פתרון מהיר במקום ללכת בדרך הנכונה, וטוב שעצרת אותי.

    הבעיה הנוכחית שלנו היא שה-BaseWorker רץ ברקע, שואב משימות מהתור, מריץ את process_task, אבל לא שומר את ה-return באף מקום (כי תכננו במקור לשמור ישירות לדאטה-בייס מתוך הפונקציה).

    כדי לבדוק את הלוגיקה של SummarizerAgent בצורה נקייה, אנחנו פשוט לא צריכים את התור (Queue) עבור הטסט הספציפי הזה. אנחנו יכולים, וצריכים, לקרוא ישירות למתודה process_task מתוך הטסט, לתפוס את התוצאה שהיא מחזירה, ולהדפיס אותה שם. ככה הפונקציה נשארת טהורה.

    הנה ה-test_summarizer.py המעודכן, שעושה בדיוק את זה:

    Python
    import asyncio
    import json
    from summarizer_agent import SummarizerAgent

    async def run_test():
        print("Starting the test environment...")

    עכשיו אתה יכול להריץ את הטסט הזה עם הטקסט שלך. הקוד של הסוכן יישאר בדיוק כמו שהוא.

    מחכה לשמוע איך עברה ההרצה ואיזה JSON ג'מיני זרק לנו חזרה!
    """

    # Create the payload with the desired summary lengths
    payload = {
        "data": sample_text,
        "summary_type": [40, 150] 
    }
    
    print("Sending task directly to process_task for testing...")
    
    # Calling process_task directly, bypassing the queue loop just for the test
    # This allows us to capture the return value cleanly without modifying the agent
    result = await agent.process_task(payload)
    
    print("\n--- Test Results ---")
    # Print the result beautifully in the test script
    print(json.dumps(result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    # Run the main async loop
    asyncio.run(run_test())

