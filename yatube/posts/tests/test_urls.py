from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа, Тестовая группа',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_group_profile_posts_url_exists_at_desired_location(self):
        """Страницы /, /group/<slug>/, profile/<username>/,
         posts/<post_id>/ доступна любому пользователю."""
        pages = ['/', f'/group/{PostModelTest.group.slug}/',
                 f'/profile/{PostModelTest.post.author}/',
                 f'/posts/{PostModelTest.post.pk}/']
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_edit_create_available_to_the_author_and_authorized(self):
        """Страница /posts/<post_id>/edit/ доступна автору, а /create/
        авторизованному пользователю"""
        pages = [f'/posts/{PostModelTest.post.pk}/edit/', '/create/']
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_existent_page_returns_404(self):
        """Несуществующая страница возвращает ошибку 404"""
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{PostModelTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostModelTest.post.author}/': 'posts/profile.html',
            f'/posts/{PostModelTest.post.pk}/': 'posts/post_detail.html',
            f'/posts/{PostModelTest.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
