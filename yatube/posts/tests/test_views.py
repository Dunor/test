from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='new_slug',
            description='Тестовое описание2',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа, Тестовая группа',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': [reverse('posts:index')],
            'posts/group_list.html': [
                reverse('posts:group_list',
                        kwargs={'slug': PostPagesTests.group.slug})
            ],
            'posts/profile.html': [
                reverse('posts:profile',
                        kwargs={'username': PostPagesTests.user.username})
            ],
            'posts/post_detail.html': [
                reverse('posts:post_detail',
                        kwargs={'post_id': PostPagesTests.post.pk})
            ],
            'posts/create_post.html': [
                reverse('posts:post_edit',
                        kwargs={'post_id': PostPagesTests.post.pk}),
                reverse('posts:post_create'),
            ],
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                for rn in reverse_name:
                    response = self.authorized_client.get(rn)
                    self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы с правильным
        контекстом."""
        templates_page_names = {
            'index': reverse('posts:index'),
            'group_list': reverse('posts:group_list',
                                  kwargs={'slug': PostPagesTests.group.slug}),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_id = first_object.id
                post_group_title = first_object.group.title
                post_group_slug = first_object.group.slug
                post_author = first_object.author.username
                post_text = first_object.text
                post_image = first_object.image
                self.assertEqual(post_id, PostPagesTests.post.pk),
                self.assertEqual(post_group_title,
                                 PostPagesTests.post.group.title)
                self.assertEqual(post_group_slug,
                                 PostPagesTests.post.group.slug)
                self.assertEqual(post_author, PostPagesTests.user.username)
                self.assertEqual(post_text, PostPagesTests.post.text)
                self.assertEqual(post_image, PostPagesTests.post.image)

    def test_post_not_fall_another_group(self):
        """Пост не попадает в другие группы"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group2.slug}))
        self.assertNotIn(PostPagesTests.post, response.context['page_obj'])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.pk}))
        self.assertEqual(response.context['post'].id, PostPagesTests.post.pk)
        self.assertEqual(
            response.context['post'].image, PostPagesTests.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        revers_list = [
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.pk}),
            reverse('posts:post_create'),
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for rev in revers_list:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    response = self.authorized_client.get(rev)
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        [Post.objects.create(author=cls.user, text=f'text {i}',
                             group=cls.group) for i in range(1, 15)]

    def setUp(self):
        self.guest_client = Client()
        self.templates_page_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username}),
        }

    def test_first_page_contains_ten_records(self):
        for template, reverse_name in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POST_COUNT)

    def test_second_page_contains_four_records(self):
        for template, reverse_name in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    Post.objects.all().count() - settings.POST_COUNT)
