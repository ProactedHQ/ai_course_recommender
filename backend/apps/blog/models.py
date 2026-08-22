from django.db import models
from django.conf import settings

class BlogLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blog_likes',
        null=True,
        blank=True
    )
    blog_slug = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # For authenticated users, ensure one like per slug.
        # For guests, we'll handle uniqueness via session/IP in the view logic for more flexibility.
        verbose_name = "Blog Like"
        verbose_name_plural = "Blog Likes"

    def __str__(self):
        liker = self.user.username if self.user else f"Guest ({self.ip_address})"
        return f"{liker} liked {self.blog_slug}"

class BlogView(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blog_views',
        null=True, 
        blank=True
    )
    blog_slug = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Blog View"
        verbose_name_plural = "Blog Views"

    def __str__(self):
        viewer = self.user.username if self.user else f"Guest ({self.ip_address})"
        return f"{viewer} viewed {self.blog_slug}"
