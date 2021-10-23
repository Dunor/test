import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='коммент к посту',
            post=cls.post,
            author=User.objects.create_user(username='user1')
        )
        cls.form = PostForm()


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
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
            'text': 'any text',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                id=Post.objects.order_by('-id')[0].id,
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif',
            ).exists()
        )

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
        происходит изменение поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'any text2',
            'group': PostFormTests.post.group.pk
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=(PostFormTests.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=PostFormTests.post.pk,
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )

    def test_post_edit_by_guest(self):
        """Измение поста анонимным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'any text3',
            'group': PostFormTests.post.group.pk
        }
        self.client.post(
            reverse('posts:post_edit', args=(PostFormTests.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                id=PostFormTests.post.pk,
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )

    def test_post_create_by_guest(self):
        """Создание поста анонимным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'any text4',
            'group': PostFormTests.group.pk
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                id=Post.objects.order_by('-id')[0].id,
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )

    def test_comment_create_by_guest(self):
        """Создание коммента анонимным пользователем"""
        comment_count = PostFormTests.post.comments.count()
        form_data = {
            'text': 'bad comment',
        }
        self.client.post(
            reverse('posts:add_comment', args=(PostFormTests.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(PostFormTests.post.comments.count(), comment_count)
        self.assertFalse(
            PostFormTests.post.comments.filter(
                id=PostFormTests.post.comments.order_by('-id')[0].id,
                text=form_data['text'],
            ).exists()
        )

    def test_comment_create_by_guest(self):
            """Создание коммента анонимным пользователем"""
            comment_count = PostFormTests.post.comments.count()
            form_data = {
                'text': 'bad comment',
            }
            self.client.post(
                reverse('posts:add_comment', args=(PostFormTests.post.pk,)),
                data=form_data,
                follow=True
            )
            self.assertEqual(PostFormTests.post.comments.count(), comment_count)
            self.assertFalse(
                PostFormTests.post.comments.filter(
                    id=PostFormTests.post.comments.order_by('-id')[0].id,
                    text=form_data['text'],
                ).exists()
            )
