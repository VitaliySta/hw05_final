import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='new-user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = User.objects.create_user(username='auth')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_text',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='test-comment',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='smalll.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'new_test_text',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group_id=self.group.pk,
                text=form_data['text'],
                image=f'posts/{uploaded.name}'
            ).exists()
        )

    def test_author_of_the_post_can_edit_it(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'new_text',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post_new = Post.objects.get(id=self.post.pk)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post_new.text, form_data['text'])
        self.assertEqual(post_new.group.title, self.group.title)
        self.assertEqual(post_new.image, f'posts/{uploaded.name}')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_author_of_the_post_cannot_edit_it(self):
        author2 = User.objects.create_user(username='new author')
        author2_client = Client()
        author2_client.force_login(author2)
        form_data = {
            'text': 'new_text',
            'group': self.group.id
        }
        response = author2_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count() + 1
        form_data = {
            'username': 'Odin',
            'password1': 'EFs6Fdacv',
            'password2': 'EFs6Fdacv',
        }
        self.guest_client.post(
            reverse('users:signup'), data=form_data, follow=True
        )
        self.assertEqual(User.objects.count(), users_count)

    def test_authorized_user_can_comment_on_the_post(self):
        comments_count = Comment.objects.count() + 1
        form_data = {
            'text': 'comment-for-post',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        post = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            post.context['comments'].last().text, form_data['text']
        )

    def test_guest_user_cannot_comment_on_the_post(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'comment-for-post',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
