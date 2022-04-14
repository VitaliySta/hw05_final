from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_text',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='One')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_available_to_everyone_exists_at_desired_location(self):
        url_name_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.group.id}/': HTTPStatus.OK,
            '/unexisting_page': HTTPStatus.NOT_FOUND,
        }
        for address, status in url_name_status.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        response = self.author_client.get(f'/posts/{self.group.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_redirect_anonymous_on_admin_login(self):
        url_names_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.group.id}/edit/':
                f'/auth/login/?next=/posts/{self.group.id}/edit/',
        }
        for address, redirect in url_names_redirect.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect)

    def test_post_edit_url_redirect_authorized_not_author_post(self):
        response = self.authorized_client.get(
            f'/posts/{self.group.id}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{self.group.id}/')

    def test_urls_uses_correct_template(self):
        url_names_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.group.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.group.id}/edit/': 'posts/create_post.html',
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
