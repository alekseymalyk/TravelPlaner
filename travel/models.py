from django.db import models


class TravelProject(models.Model):
    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        COMPLETED = 'completed', 'Completed'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def has_visited_places(self):
        return self.places.filter(visited=True).exists()

    def recalculate_status(self):
        """Mark the project completed once all of its places are visited."""
        places = self.places.all()
        all_visited = places.exists() and not places.filter(visited=False).exists()
        new_status = self.Status.COMPLETED if all_visited else self.Status.PLANNING
        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])


class Place(models.Model):
    project = models.ForeignKey(
        TravelProject,
        related_name='places',
        on_delete=models.CASCADE,
    )
    external_id = models.CharField(max_length=64)
    title = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    visited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'external_id'],
                name='unique_place_per_project',
            ),
        ]

    def __str__(self):
        return f'{self.title or self.external_id} ({self.project_id})'
