from courses.models import BlockCards
def update_block_cards(instance, chips_data, s3):
    existing_chip_ids = set(instance.chips.values_list('id', flat=True))
    new_chip_ids = set()
    chips_objs = []

    for chip_data in chips_data:
        chip_id = chip_data.get('id')
        if chip_id and chip_id != -1:
            chip, _ = BlockCards.objects.update_or_create(
                id=chip_id,
                defaults={
                    'title': chip_data.get('title'),
                    'description': chip_data.get('description'),
                    'position': chip_data.get('position'),
                }
            )
            new_chip_ids.add(chip.id)
        else:
            chip = BlockCards.objects.create(
                title=chip_data.get('title'),
                description=chip_data.get('description'),
                position=chip_data.get('position'),
            )
            new_chip_ids.add(chip.id)

        chips_objs.append(chip)

    instance.chips.set(chips_objs)
    instance.save()

    # Удаление старых несвязанных объектов
    unlink_chip_ids = existing_chip_ids - new_chip_ids
    for chip_id in unlink_chip_ids:
        chip = BlockCards.objects.get(id=chip_id)
        # Удаление изображения из хранилища
        if chip.photo:
            s3.delete_file(str(chip.photo))
        if not (chip in instance.chips.all()):
            chip.delete()
