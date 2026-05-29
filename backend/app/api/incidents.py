from fastapi import APIRouter

router = APIRouter()

@router.get('/incidents')
def get_incidents():
    return [
        {
            'id': 1,
            'title': 'Payment Service Outage',
            'status': 'resolved'
        }
    ]