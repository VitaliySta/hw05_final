import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_text',
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='One')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
        }
        for reverse_name, template, in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def verify_post_context(self, first_object):
        self.assertEqual(first_object.group, PostsViewsTests.post.group)
        self.assertEqual(first_object.text, PostsViewsTests.post.text)
        self.assertEqual(first_object.author, PostsViewsTests.post.author)
        self.assertEqual(first_object.image, PostsViewsTests.post.image)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.verify_post_context(first_object)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.verify_post_context(first_object)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author})
        )
        first_object = response.context['page_obj'][0]
        self.verify_post_context(first_object)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1})
        )
        first_object = response.context['post']
        post_text = first_object.text
        post_id = first_object.id
        post_image = first_object.image
        self.assertEqual(post_text, PostsViewsTests.post.text)
        self.assertEqual(post_id, 1)
        self.assertEqual(post_image, PostsViewsTests.post.image)

    def test_create_post_edit_show_correct_context(self):
        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 1})
        )
        first_object = response.context['post']
        post_id = first_object.id
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(post_id, 1)

    def test_create_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_correct_group(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        self.assertEqual(post_text, PostsViewsTests.post.text)

    def test_cache(self):
        response1 = self.client.get(reverse('posts:index')).content
        self.post.delete()
        response2 = self.client.get(reverse('posts:index')).content
        self.assertEqual(response1, response2)
        cache.clear()
        response3 = self.client.get(reverse('posts:index')).content
        self.assertNotEqual(response1, response3)

    def test_new_user_post_appears_in_the_feed_of_those_who_follow_him(self):
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].text, self.post.text)

    def test_new_post_does_not_appear_in_the_feed_who_are_not_following(self):
        user = User.objects.create_user(username='Elena')
        authorized_client = Client()
        authorized_client.force_login(user)
        Follow.objects.create(
            user=user,
            author=self.author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_authorized_user_can_follow_other_users(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertEqual(
            Follow.objects.get(user=self.user).author, self.author
        )

    def test_authorized_user_can_unfollow_other_users(self):
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
        )
        posts = [
            Post(
                author=cls.author, text=f'test_text {i}',
                group=cls.group
            )
            for i in range(13)
        ]
        Post.objects.bulk_create(posts)

    def test_page_contains_ten_records(self):
        reverses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        for url in reverses:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.PAGINATION_NUMBER
                )

    def test_page_contains_three_records(self):
        posts_count = Post.objects.count()
        reverses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        for url in reverses:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_count - settings.PAGINATION_NUMBER
                )
