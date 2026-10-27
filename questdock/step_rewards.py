"""Per-step rewards use a high-water mark, so undo/repeat cannot farm coins."""
def unpaid_steps(task):
    paid=task.get('rewarded_steps',task['target'] if task['claimed'] else 0)
    return max(0,min(task['progress'],task['target'])-paid)


def pay_steps(data,task):
    count=unpaid_steps(task)
    amount=count*task['reward']
    task['rewarded_steps']=max(task.get('rewarded_steps',task['target'] if task['claimed'] else 0),task['progress'])
    task['claimed']=task['progress']>=task['target']
    data['coins']+=amount;data['earned']+=amount
    return count,amount
