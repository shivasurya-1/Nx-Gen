
from courses.models import Assignment
assignments = Assignment.objects.filter(instructor__isnull=True)
count = 0
for a in assignments:
    if a.batch and a.batch.instructor:
        a.instructor = a.batch.instructor
        a.save()
        count += 1
print(f"Successfully backfilled {count} assignments.")
