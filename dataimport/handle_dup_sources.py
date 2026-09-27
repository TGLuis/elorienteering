import elo.models
from elo.fields import SourceType
from elo.models import Runner, Source

def get_duplicates_in_file(filename):
    dups = {}
    with open(filename, encoding="utf8") as f:
        lines = f.readlines()
    for line in lines:
        names = line.split(",")
        dups[names[0]] = names[1:]
    return dups

def redirect_source_to_runner(dups: dict, source_type: SourceType):
    for runner_name, source_names in dups.items():
        runner = Runner.objects.get(fullname=runner_name)
        for source_name in source_names:
            try:
                source = Source.objects.get(source_type=source_type, fullname_in_source=source_name.strip())
                source.runner = runner
                source.save()
            except elo.models.Source.DoesNotExist:
                print(f"'{source_name}' in {source_type.label} does not exist")

def main():
    redirect_source_to_runner(get_duplicates_in_file("dataimport/data/merges-helga.txt"), SourceType.HELGA_WEBRES)

    # TODO maybe one day, delete runners without sources ?

if __name__ == "__main__":
    main()