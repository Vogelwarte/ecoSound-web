let uploadDir = Math.floor(Math.random() * (10000000 - 100000) + 100000);

$("#file-uploader").pluploadQueue({
    runtimes: 'html5',
    url: baseUrl + '/scripts/uploaded.php?dir=' + uploadDir,
    max_file_size: '1000mb',
    chunk_size: '1mb',
    unique_names: false,
    multiple_queues: true,
    prevent_duplicates: true,
    filters: {
        max_file_size: '1000mb',
        mime_types: [
            {title: "Recording files", extensions: "flac,wav,ogg,mp3"}
        ]
    },
    init: {
        UploadComplete: function (up) {
            $("#save_button").prop("disabled", false);
        },
        Error: function (up, args) {
            showAlert(args.message.replace(/\.([^\.]*)$/, ": $1") + args.file.name);
        },
        FilesAdded: function (up, files) {
            plupload.each(files, function (file) {
                if (file.name.replace(/\.[^/.]+$/, "").length > 150) {
                    $(".plupload_start").addClass('plupload_disabled');
                    up.removeFile(file);
                    showAlert('File name: ' + file.name + ' too long. Maximum: 150 characters. File was skipped.', true);
                }
            });
            if (up.files.length > 0) {
                document.querySelector('.plupload_start').click();
                $('#uploadForm').collapse('show');
                $("#save_button").prop("disabled", true);
            }
        }
    }
});

$('#uploadForm')
    .submit(function (e) {
        $("#save_button").prop("disabled", true);
        let values = new FormData($(this)[0]);
        values["colID"] = $("#collection").val();

        postRequest(
            baseUrl + '/api/file/upload/' + uploadDir,
            values,
            true,
            true,
            function (response) {
                $('#upload_btn').toggle();
                if (response.error_code == 0) {
                    location.reload();
                }
            })
        e.preventDefault();
    })

$("#reference").change(function (e) {
    let referenceFields = $('.js-reference-field');
    let requiredFields = $('.js-field-required');
    referenceFields.prop('disabled', !referenceFields.prop('disabled'));
    requiredFields.prop('required', !requiredFields.prop('required'));
});

$("#from-file").change(function (e) {
    let fileFields = $('.js-file-field');
    fileFields.prop('disabled', !fileFields.prop('disabled'));
    fileFields.prop('required', !fileFields.prop('required'));
});


$(function () {

    $("#metaDataButton").on("click", function () {
        $("#metaDataFile").click();
    })

    $("#metaDataFile").on("change", function () {
        analysisList(this.files);
    })

    function analysisList(obj) {
        if (obj.length < 1) {
            return false;
        }
        var fileObj = obj[0];
        var name = fileObj.name;
        var size = fileObj.size;
        var type = fileType(name);
        if (("csv").indexOf(type) == -1) {
            showAlert(name + ' file type error.');
            return
        }
        if (size > 5 * 1024 * 1024 || size == 0) {
            showAlert(name + ' file size exceeds 5M.');
            return
        }
        toggleLoading();
        $.ajax({
            url: baseUrl + '/api/file/metadata',
            type: "POST",
            data: new FormData($("#metaDataForm")[0]),
            processData: false,
            contentType: false,
            success: function (result) {
                if (result.message == 'Upload success.') {
                    location.reload();
                } else {
                    showAlert(result.message)
                    $('#metaDataFile').val('')
                    toggleLoading();
                }
            },
            error: function () {
                showAlert("Failed to upload file.")
                toggleLoading();
            }
        });
    }

    function fileType(name) {
        var nameArr = name.split(".");
        return nameArr[nameArr.length - 1].toLowerCase();
    }
})