def dockerfile_generate(input_path: str, output_path: str, base_image: str = None, new_version: str = None) -> None:
    """
    Generate a new Dockerfile based on an existing one, optionally updating the base image and version.

    Parameters:
    - input_path: The path to the original Dockerfile.
    - output_path: The path to save the new Dockerfile.
    - base_image: The new base image to use in the Dockerfile (optional).
    - new_version: The new version to set for the BASE_VERSION argument (optional).
    """
    # check the input
    if not input_path:
        raise ValueError("input_path must not be empty")
    
    if not output_path:
        raise ValueError("output_path must not be empty")

    if not new_version:
        raise ValueError("new_version must not be empty")

    try:
        with open(input_path, 'r') as file:
            dockerfile_lines = file.readlines()

        new_dockerfile_lines = []

        # add the new base image in need
        if base_image:
            new_dockerfile_lines.append(f'FROM {base_image}\n')

        # updating the BASE_VERSION
        for line in dockerfile_lines:
            stripped_line = line.strip()
            if stripped_line.startswith('ARG BASE_VERSION'):
                new_dockerfile_lines.append(f'ARG BASE_VERSION={new_version}\n')
            else:
                new_dockerfile_lines.append(line)

        with open(output_path, 'w') as file:
            file.writelines(new_dockerfile_lines)

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}. Check that the input file path is correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
