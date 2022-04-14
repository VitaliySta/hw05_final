from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост проверка',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        expexted_object_name = post.text[:15]
        self.assertEqual(expexted_object_name, str(post))

        group = PostModelTest.group
        expexted_object_name = group.title
        self.assertEqual(expexted_object_name, str(group))
