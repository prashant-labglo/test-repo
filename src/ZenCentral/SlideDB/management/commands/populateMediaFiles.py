from django.core.management.base import BaseCommand
from django.core.files import File
from urllib.request import urlretrieve, urlcleanup
from SlideDB.models import Slide


class Command(BaseCommand):
    """
    Command to populate the media files i.e pptx and image files for each slide from the URLs.
    """
    def handle(self, *args, **options):

        slides_list = Slide.objects.all()

        for slide in slides_list:
            # Define image file name
            image_name = slide.thumbnailFile.split("/")[-1]

            # Define pptx file name
            file_name = slide.pptFile.split("/")[-1]

            try:
                # Retrieve pptx file from url and save it into new file field.
                ppt_file, _ = urlretrieve(slide.pptFile)
                slide.pptxFile.save(file_name, File(open(ppt_file, 'rb')))

                # Retrieve image file from url and save it into new image field.
                image_file, _ = urlretrieve(slide.thumbnailFile)
                slide.imageFile.save(image_name, File(open(image_file, 'rb')))

                slide.save()
                print("==>Saved Files For Slide ID : ", slide.id)
            finally:
                urlcleanup()
