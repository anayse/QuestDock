"""Generic test-only tasks; never imported by the application."""
import app


def sample_data():
    data=app.initial()
    data['tasks']=[app.task('测试任务 '+str(i+1),app.TYPES[0 if i<6 else 1 if i<8 else i-6],
                            '用于自动测试的通用内容',3 if i==1 else 5 if i==8 else 1,
                            30 if i==1 else 300 if i==8 else 20) for i in range(10)]
    return data
