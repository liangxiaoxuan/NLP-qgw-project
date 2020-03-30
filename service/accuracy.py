"""
统计委派部门的正确率
"""
from qgw_autoflow.dao.model import load_session, CaseRepo, CaseAssignTier, CaseFinishTier

db = load_session()


def assign():
    case_repo = db.query(CaseRepo).filter(CaseRepo.finish_depart.isnot(None)).filter(CaseRepo.update_time.between('2017-07-11 00:00:00', '2018-07-21 00:00:00')).all()
    all = case_repo.__len__()
    accur = 0.0
    print('总量:', all)
    assign = db.query(CaseAssignTier.depart_id).filter(CaseAssignTier.tier == 2)
    finish = db.query(CaseFinishTier.depart_id).filter(CaseFinishTier.tier == 2)
    for case in case_repo:
        a = assign.filter(CaseAssignTier.case_repo_id == case.id).all()
        f = finish.filter(CaseFinishTier.case_repo_id == case.id).all()
        for item in f:
            if item in a:
                accur += 1
                break

    print('正确数：', accur)
    print('正确率：', accur / all)
    pass


if __name__ == '__main__':
    assign()
